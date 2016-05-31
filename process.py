import os, re

METHOD_INDEX = 1
REQUESTID_INDEX = 2
URL_INDEX = 3
MIMETYPE_INDEX = 4
DATASIZE_INDEX = 5
ENCODED_DATASIZE_INDEX = 6
TIMESTAMP_INDEX = 7
PROTOCOL_INDEX = 8


def preprocess(table, filename):
    filename = filename.split("_")[0]
    # print filename

    while not filename in table[0][URL_INDEX]:
        del table[0]

    while not table[-1][0] or "loadEventFired" not in table[-1][METHOD_INDEX]:
        del table[-1]

    return table


def process_handshake(table):
    request_sent = float(table[0][TIMESTAMP_INDEX])
    index = 0

    while not "responseReceived" in table[index][METHOD_INDEX]:
        index += 1

    response_received = float(table[index][TIMESTAMP_INDEX])

    return response_received - request_sent


def process_page_load_time(table):
    request_sent = float(table[0][TIMESTAMP_INDEX])
    page_loaded = float(table[-1][TIMESTAMP_INDEX])

    return page_loaded - request_sent


def process_DOM_load_time(table):
    request_sent = float(table[0][TIMESTAMP_INDEX])
    index = 0

    while index < len(table) and not "domContentEventFired" in table[index][METHOD_INDEX]:
        index += 1

    if index == len(table):
        # When DOM is loaded simultaneously with the page
        dom_loaded = float(table[-1][TIMESTAMP_INDEX])
    else:
        dom_loaded = float(table[index][TIMESTAMP_INDEX])

    return dom_loaded - request_sent


def process_mimetypes(table):
    # Collects info about # of each mimetype, their sizes, their encoded sizes and time for download.

    plaintext, html, js_css, img_others = 0, 0, 0, 0
    plaintext_encoded, html_encoded, js_css_encoded, img_others_encoded = 0, 0, 0, 0
    plaintext_size, html_size, js_css_size, img_others_size = 0, 0, 0, 0
    plaintext_time, html_time, js_css_time, img_others_time = 0, 0, 0, 0

    id_dict = {}

    for row in table:
        request_id = row[REQUESTID_INDEX]

        if not request_id in id_dict:
            id_dict[request_id] = [None, None, None, None]

        if "requestWillBeSent" in row[METHOD_INDEX]:
            if not id_dict[request_id][-1]:
                id_dict[request_id][-1] = float(row[TIMESTAMP_INDEX])

        if "responseReceived" in row[METHOD_INDEX]:
            id_dict[request_id][0] = row[MIMETYPE_INDEX]

        if "dataReceived" in row[METHOD_INDEX]:
            if id_dict[request_id][1]:
                id_dict[request_id][1] += int(row[DATASIZE_INDEX])
            else:
                id_dict[request_id][1] = int(row[DATASIZE_INDEX])

        if "loadingFinished" in row[METHOD_INDEX]:
            id_dict[request_id][2] = int(row[ENCODED_DATASIZE_INDEX])
            id_dict[request_id][-1] = float(row[TIMESTAMP_INDEX]) - id_dict[request_id][-1]

    for key in id_dict:
        lst = id_dict[key]

        mimetype = lst[0]
        size = lst[1]
        encoded_datasize = lst[2]
        time = lst[-1]

        # Filter degenerate cases with no "loadingFinished" tag
        if not encoded_datasize or not size:
            continue

        if mimetype == "text/plain":
            plaintext += 1
            plaintext_encoded += encoded_datasize
            plaintext_size += size
            plaintext_time += time

        elif "javascript" in mimetype or "css" in mimetype:
            js_css += 1
            js_css_encoded += encoded_datasize
            js_css_size += size
            js_css_time += time

        elif "html" in mimetype:
            html += 1
            html_encoded += encoded_datasize
            html_size += size
            html_time += time

        else:
            img_others += 1
            img_others_encoded += encoded_datasize
            img_others_size += size
            img_others_time += time

    return (plaintext, plaintext_encoded, plaintext_size, plaintext_time,
            js_css, js_css_encoded, js_css_size, js_css_time,
            html, html_encoded, html_size, html_time,
            img_others, img_others_encoded, img_others_size, img_others_time)


def process_domains(table):
    domain_list = []

    for row in table:
        domain_list.append(row[URL_INDEX])

    return len(set(domain_list))


def process_datasize(table):
    return 0, 0


def dump(table):
    domain_list = []

    for row in table:
        domain_list.append(row[URL_INDEX])

    f = open("domains.txt", "a")

    for dom in domain_list:
        f.write(dom + "\n")

    pass


def process(dir="rawdata/"):
    data_files = filter(
        lambda x: re.match(".+csv$", x),
        os.listdir(dir))

    header = ["Protocol", "Site", "HandshakeTime", "PageLoadTime", "DOMLoadTime",
              "No.Plaintexts", "PlaintextsEncodedSize", "PlaintextsSize", "PlaintextsLoadTime",
              "HTML", "HTMLEncodedSize", "HTMLSize", "HTMLLoadTime",
              "JS/CSS", "JS/CSSEncodedSize", "JS/CSSSize", "JS/CSSLoadTime",
              "Images/Others", "Images/OthersEncodedSize", "Images/OthersSize", "Images/OthersLoadTime",
              "Domains", "EncodedDataSize", "TotalDataSize"]

    g = open("statistics.csv", "a")
    g.write(",".join(header) + "\n")

    for filename in data_files:
        f = open(dir + filename, "r")
        _table = f.read().split("\n")
        table = []

        for _t in _table:
            table.append(_t.split(","))

        table = preprocess(table, filename)

        protocol = filename.split("_")[1]
        site = filename.split("_")[0]
        handshake_time = process_handshake(table)
        page_load_time = process_page_load_time(table)
        DOM_load_time = process_DOM_load_time(table)
        (
            plaintext, plaintext_encoded, plaintext_size, plaintext_time,
            js_css, js_css_encoded, js_css_size, js_css_time,
            html, html_encoded, html_size, html_time,
            img_others, img_others_encoded, img_others_size, img_others_time
        ) = process_mimetypes(table)
        domains = process_domains(table)
        datasize_encoded = plaintext_encoded + js_css_encoded + html_encoded + img_others_encoded
        datasize = plaintext_size + js_css_size + html_size + img_others_size

        g.write(",".join(
                [
                    str(protocol), str(site), str(handshake_time), str(page_load_time), str(DOM_load_time),
                    str(plaintext), str(plaintext_encoded), str(plaintext_size), str(plaintext_time),
                    str(html), str(html_encoded), str(html_size), str(html_time),
                    str(js_css), str(js_css_encoded), str(js_css_size), str(js_css_time),
                    str(img_others), str(img_others_encoded), str(img_others_size), str(img_others_time),
                    str(domains), str(datasize_encoded), str(datasize)
                ]
            ) + "\n"
        )

        f.close()

        # dump(table)
        #
        # h = open("domains.txt", "r")
        # f = open("domain.txt", "w")
        #
        # dom = set(filter(lambda x: x and "." in x, h.read().split("\n")))
        #
        # for d in dom:
        #     f.write(d + "\n")
        #
        # f.close()
        # h.close()

    g.close()


if __name__ == "__main__":
    process()


















