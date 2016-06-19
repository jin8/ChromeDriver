package main

import (
	"bufio"
	"bytes"
	"compress/gzip"
	"crypto/tls"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/devsisters/goquic"

	"golang.org/x/net/html"
)

var hostMap = make(map[string]string)
var domainSuffix = ".this"

// onExitFlushLoop is a callback set by tests to detect the state of the
// flushLoop() goroutine.
var onExitFlushLoop func()

// ReverseProxy is an HTTP Handler that takes an incoming request and
// sends it to another server, proxying the response back to the
// client.
type ReverseProxy struct {
	// Director must be a function which modifies
	// the request into a new request to be sent
	// using Transport. Its response is then copied
	// back to the original client unmodified.
	Director func(*http.Request)

	// The transport used to perform proxy requests.
	// If nil, http.DefaultTransport is used.
	Transport http.RoundTripper

	// FlushInterval specifies the flush interval
	// to flush to the client while copying the
	// response body.
	// If zero, no periodic flushing is done.
	FlushInterval time.Duration

	// ErrorLog specifies an optional logger for errors
	// that occur when attempting to proxy the request.
	// If nil, logging goes to os.Stderr via the log package's
	// standard logger.
	ErrorLog *log.Logger

	// BufferPool optionally specifies a buffer pool to
	// get byte slices for use by io.CopyBuffer when
	// copying HTTP response bodies.
	BufferPool BufferPool
}

// A BufferPool is an interface for getting and returning temporary
// byte slices for use by io.CopyBuffer.
type BufferPool interface {
	Get() []byte
	Put([]byte)
}

func singleJoiningSlash(a, b string) string {
	aslash := strings.HasSuffix(a, "/")
	bslash := strings.HasPrefix(b, "/")
	switch {
	case aslash && bslash:
		return a + b[1:]
	case !aslash && !bslash:
		return a + "/" + b
	}
	return a + b
}

func copyHeader(dst, src http.Header) {
	for k, vv := range src {
		for _, v := range vv {
			dst.Add(k, v)
		}
	}
}

// Hop-by-hop headers. These are removed when sent to the backend.
// http://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html
var hopHeaders = []string{
	"Connection",
	"Proxy-Connection", // non-standard but still sent by libcurl and rejected by e.g. google
	"Keep-Alive",
	"Proxy-Authenticate",
	"Proxy-Authorization",
	"Te",      // canonicalized version of "TE"
	"Trailer", // not Trailers per URL above; http://www.rfc-editor.org/errata_search.php?eid=4522
	"Transfer-Encoding",
	"Upgrade",
}

type requestCanceler interface {
	CancelRequest(*http.Request)
}

type runOnFirstRead struct {
	io.Reader // optional; nil means empty body

	fn func() // Run before first Read, then set to nil
}

func (c *runOnFirstRead) Read(bs []byte) (int, error) {
	if c.fn != nil {
		c.fn()
		c.fn = nil
	}
	if c.Reader == nil {
		return 0, io.EOF
	}
	return c.Reader.Read(bs)
}

func (p *ReverseProxy) ServeHTTP(rw http.ResponseWriter, req *http.Request) {
	transport := p.Transport
	if transport == nil {
		transport = http.DefaultTransport
	}

	outreq := new(http.Request)
	*outreq = *req // includes shallow copies of maps, but okay

	if closeNotifier, ok := rw.(http.CloseNotifier); ok {
		if requestCanceler, ok := transport.(requestCanceler); ok {
			reqDone := make(chan struct{})
			defer close(reqDone)

			clientGone := closeNotifier.CloseNotify()

			outreq.Body = struct {
				io.Reader
				io.Closer
			}{
				Reader: &runOnFirstRead{
					Reader: outreq.Body,
					fn: func() {
						go func() {
							select {
							case <-clientGone:
								requestCanceler.CancelRequest(outreq)
							case <-reqDone:
							}
						}()
					},
				},
				Closer: outreq.Body,
			}
		}
	}

	p.Director(outreq)
	outreq.Proto = "HTTP/1.1"
	outreq.ProtoMajor = 1
	outreq.ProtoMinor = 1
	outreq.Close = false

	// Remove hop-by-hop headers to the backend.  Especially
	// important is "Connection" because we want a persistent
	// connection, regardless of what the client sent to us.  This
	// is modifying the same underlying map from req (shallow
	// copied above) so we only copy it if necessary.
	copiedHeaders := false
	for _, h := range hopHeaders {
		if outreq.Header.Get(h) != "" {
			if !copiedHeaders {
				outreq.Header = make(http.Header)
				copyHeader(outreq.Header, req.Header)
				copiedHeaders = true
			}
			outreq.Header.Del(h)
		}
	}

	if clientIP, _, err := net.SplitHostPort(req.RemoteAddr); err == nil {
		// If we aren't the first proxy retain prior
		// X-Forwarded-For information as a comma+space
		// separated list and fold multiple headers into one.
		if prior, ok := outreq.Header["X-Forwarded-For"]; ok {
			clientIP = strings.Join(prior, ", ") + ", " + clientIP
		}
		outreq.Header.Set("X-Forwarded-For", clientIP)
	}

	//outreq.Header.Set("Host", outreq.URL.Host)
	outreq.Host = outreq.URL.Host
	if strings.HasSuffix(outreq.URL.Host, domainSuffix) {
		outreq.Host = outreq.URL.Host[:len(outreq.URL.Host)-4]
	}
	//orgdump, _ := httputil.DumpRequest(req, false)
	//if req.URL.IsAbs() {
	//	fmt.Printf("org: %q\n", orgdump)
	//}
	//dump, _ := httputil.DumpRequestOut(outreq, false)
	//if outreq.URL.IsAbs() {
	//	fmt.Printf("out: %q\n", dump)
	//}

	res, err := transport.RoundTrip(outreq)
	if err != nil {
		p.logf("http: proxy error: %v", err)
		rw.WriteHeader(http.StatusInternalServerError)
		return
	}

	for _, h := range hopHeaders {
		res.Header.Del(h)
	}

	copyHeader(rw.Header(), res.Header)

	// The "Trailer" header isn't included in the Transport's response,
	// at least for *http.Transport. Build it up from Trailer.
	if len(res.Trailer) > 0 {
		var trailerKeys []string
		for k := range res.Trailer {
			trailerKeys = append(trailerKeys, k)
		}
		rw.Header().Add("Trailer", strings.Join(trailerKeys, ", "))
	}

	rw.WriteHeader(res.StatusCode)
	if len(res.Trailer) > 0 {
		// Force chunking if we saw a response trailer.
		// This prevents net/http from calculating the length for short
		// bodies and adding a Content-Length.
		if fl, ok := rw.(http.Flusher); ok {
			fl.Flush()
		}
	}

	// 1: Original method (bypass)
	//p.copyResponse(rw, res.Body)

	// 2: Naive replace method
	//naiveReplacer(rw, res)

	// 3: HTML parsing method
	htmlReplacer(rw, res, outreq.Host)

	res.Body.Close() // close now, instead of defer, to populate res.Trailer
	copyHeader(rw.Header(), res.Trailer)
}

func htmlReplacer(rw http.ResponseWriter, res *http.Response, host string) {
	if !strings.HasPrefix(res.Header.Get("Content-Type"), "text/html") {
		io.CopyBuffer(rw, res.Body, nil)
		return
	}

	bodyReader := io.ReadCloser(res.Body)
	if res.Header.Get("Content-Encoding") == "gzip" {
		bodyReader, _ = gzip.NewReader(bodyReader)
		defer bodyReader.Close()
	}

	bodyWriter := io.Writer(rw)
	if res.Header.Get("Content-Encoding") == "gzip" {
		gzipBodyWriter := gzip.NewWriter(rw)
		bodyWriter = gzipBodyWriter
		defer gzipBodyWriter.Close()
	}
	bodyWriter = bufio.NewWriter(bodyWriter)

	tokenizer := html.NewTokenizer(bodyReader)

outer:
	for {
		tok := tokenizer.Next()
		switch tok {
		case html.ErrorToken:
			fmt.Println("ERROR PARSING!!!!!!!!!!!!!!", tokenizer.Err())
			bodyWriter.Write([]byte(tokenizer.Raw()))
			break outer
		case html.StartTagToken:
			bodyWriter.Write([]byte("<"))
			name, hasAttr := tokenizer.TagName()
			bodyWriter.Write(name)
			if hasAttr {
				bodyWriter.Write([]byte(" "))
			}
			for hasAttr {
				var key, val []byte
				key, val, hasAttr = tokenizer.TagAttr()
				if string(key) == "href" || string(key) == "src" || string(key) == "data-src" {
					if bytes.HasPrefix(val, []byte("//")) {
						val = bytes.Join([][]byte{[]byte("https"), []byte(":"), val}, []byte(""))
					}

					val = []byte(convertToThisURL(string(val)))
				}
				bodyWriter.Write(key)
				bodyWriter.Write([]byte(fmt.Sprintf("=\"%s\"", html.EscapeString(string(val)))))
			}
			bodyWriter.Write([]byte(">"))
		case html.SelfClosingTagToken:
			bodyWriter.Write([]byte("<"))
			name, hasAttr := tokenizer.TagName()
			bodyWriter.Write(name)
			if hasAttr {
				bodyWriter.Write([]byte(" "))
			}
			for hasAttr {
				var key, val []byte
				key, val, hasAttr = tokenizer.TagAttr()
				if string(key) == "href" || string(key) == "src" || string(key) == "data-src" {
					if bytes.HasPrefix(val, []byte("//")) {
						val = bytes.Join([][]byte{[]byte("https"), []byte(":"), val}, []byte(""))
					}

					val = []byte(convertToThisURL(string(val)))
				}
				bodyWriter.Write(key)
				bodyWriter.Write([]byte(fmt.Sprintf("=\"%s\"", html.EscapeString(string(val)))))
			}
			bodyWriter.Write([]byte(">"))
		default:
			// Process the current token.
			//fmt.Println(tok)
			//fmt.Println(string(tokenizer.Raw()))
			bodyWriter.Write([]byte(tokenizer.Raw()))
		}
	}
}

func naiveReplacer(rw http.ResponseWriter, res *http.Response) {
	bodyReader := io.ReadCloser(res.Body)
	if res.Header.Get("Content-Encoding") == "gzip" {
		bodyReader, _ = gzip.NewReader(bodyReader)
		defer bodyReader.Close()
	}
	body, _ := ioutil.ReadAll(bodyReader)
	//fmt.Println(string(body[:]))
	new_body := bytes.Replace(body, []byte("clien.net"), []byte("clien.net.this"), -1)

	bodyWriter := io.Writer(rw)
	if res.Header.Get("Content-Encoding") == "gzip" {
		gzipBodyWriter := gzip.NewWriter(rw)
		bodyWriter = gzipBodyWriter
		defer gzipBodyWriter.Close()
	}

	_, err := bodyWriter.Write(new_body)
	if err != nil {
		panic(err)
	}
}

func (p *ReverseProxy) copyResponse(dst io.Writer, src io.Reader) {
	if p.FlushInterval != 0 {
		if wf, ok := dst.(writeFlusher); ok {
			mlw := &maxLatencyWriter{
				dst:     wf,
				latency: p.FlushInterval,
				done:    make(chan bool),
			}
			go mlw.flushLoop()
			defer mlw.stop()
			dst = mlw
		}
	}

	var buf []byte
	if p.BufferPool != nil {
		buf = p.BufferPool.Get()
	}
	io.CopyBuffer(dst, src, buf)
	if p.BufferPool != nil {
		p.BufferPool.Put(buf)
	}
}

func (p *ReverseProxy) logf(format string, args ...interface{}) {
	if p.ErrorLog != nil {
		p.ErrorLog.Printf(format, args...)
	} else {
		log.Printf(format, args...)
	}
}

type writeFlusher interface {
	io.Writer
	http.Flusher
}

type maxLatencyWriter struct {
	dst     writeFlusher
	latency time.Duration

	lk   sync.Mutex // protects Write + Flush
	done chan bool
}

func (m *maxLatencyWriter) Write(p []byte) (int, error) {
	m.lk.Lock()
	defer m.lk.Unlock()
	return m.dst.Write(p)
}

func (m *maxLatencyWriter) flushLoop() {
	t := time.NewTicker(m.latency)
	defer t.Stop()
	for {
		select {
		case <-m.done:
			if onExitFlushLoop != nil {
				onExitFlushLoop()
			}
			return
		case <-t.C:
			m.lk.Lock()
			m.dst.Flush()
			m.lk.Unlock()
		}
	}
}

func (m *maxLatencyWriter) stop() { m.done <- true }

func converToOrgUrlStr(urlStr string) string {
	u, err := url.Parse(urlStr)
	if err != nil || !u.IsAbs() {
		return urlStr
	}

	converToOrgUrl(u)

	return u.String()
}

func converToOrgUrl(u *url.URL) {
	host := u.Host
	port := ""
	if strings.Contains(u.Host, ":") {
		sp := strings.SplitN(u.Host, ":", 1)
		host = sp[0]
		port = sp[1]
	}

	if strings.HasSuffix(host, domainSuffix) {
		host = host[0 : len(host)-len(domainSuffix)]
	}

	if len(port) > 0 {
		u.Host = host + ":" + port
	} else {
		u.Host = host
	}

	scheme, exists := hostMap[host]
	if exists && u.Scheme == "https" {
		fmt.Println("Changing scheme of", u.Host, "to", scheme)
		u.Scheme = scheme
	}
}

func convertToThisURL(urlStr string) string {
	u, err := url.Parse(urlStr)
	if err != nil || !u.IsAbs() {
		return urlStr
	}

	host := u.Host
	port := ""
	if strings.Contains(u.Host, ":") {
		sp := strings.SplitN(u.Host, ":", 1)
		host = sp[0]
		if len(sp) > 1 {
			port = sp[1]
		}
	}

	// We are going to replace all http scheme to https since HTTP/2 and QUIC only supports https
	// So we are going to lose information about whether the original host was using http or https
	// We are marking the original scheme to hostMap
	if u.Scheme == "http" && !strings.HasSuffix(host, domainSuffix) {
		fmt.Printf("%s: %s\n", host, u.Scheme)
		hostMap[host] = u.Scheme
	}

	if !strings.HasSuffix(host, domainSuffix) {
		host = host + domainSuffix
	}
	if len(port) > 0 {
		u.Host = host + ":" + port
	} else {
		u.Host = host
	}

	if u.Scheme == "http" {
		// We are going to replace all http scheme to https since HTTP/2 and QUIC only supports https
		u.Scheme = "https"
	}

	return u.String()
}

func NewTestReverseProxy() *ReverseProxy {
	director := func(req *http.Request) {
		req.URL.Scheme = "http"
		fmt.Println("host:", req.Host)

		req.URL.Host = req.Host
		converToOrgUrl(req.URL)

		referer := req.Header.Get("referer")
		if len(referer) > 0 {
			req.Header.Set("referer", converToOrgUrlStr(referer))
		}
	}
	return &ReverseProxy{Director: director}
}

var numDispatchers int
var addr, cert, key string
var useQuic, useHttp2 bool

func init() {
	flag.IntVar(&numDispatchers, "n", 1, "Number of concurrent quic dispatchers")
	flag.StringVar(&addr, "addr", ":443", "TCP/UDP host/port to bind")
	flag.StringVar(&cert, "cert", "server.crt", "Certificate file (PEM), will use encrypted QUIC and TLS when provided")
	flag.StringVar(&key, "key", "server.key", "Private key file (PEM), will use encrypted QUIC and TLS when provided")
	flag.BoolVar(&useQuic, "quic", true, "Use QUIC (implies HTTP2)")
	flag.BoolVar(&useHttp2, "http2", true, "Use HTTP2")

	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s -cert ... -key ...\n", os.Args[0])
		fmt.Fprintf(os.Stderr, "Options:\n")
		flag.PrintDefaults()
	}
}

func main() {
	flag.Parse()
	proxyHandler := NewTestReverseProxy()
	if !useQuic {
		server := &http.Server{
			Addr:           addr,
			Handler:        proxyHandler,
			ReadTimeout:    10 * time.Second,
			WriteTimeout:   10 * time.Second,
			MaxHeaderBytes: 1 << 20,
		}
		server.ListenAndServeTLS(cert, key)
	} else {
		quicServer, err := goquic.NewServer(addr, cert, key, numDispatchers, proxyHandler, proxyHandler, &tls.Config{})
		if err != nil {
			panic(err)
		}
		quicServer.ListenAndServe()
	}
}
