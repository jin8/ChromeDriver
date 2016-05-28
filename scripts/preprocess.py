import os, re

METHOD_INDEX = 1
REQUESTID_INDEX = 2
URL_INDEX = 3
MIMETYPE_INDEX = 4
DATASIZE_INDEX = 5
ENCODED_DATASIZE_INDEX = 6
TIMESTAMP_INDEX = 7
PROTOCOL_INDEX = 8


def process_handshake(table, filename):
    request_sent = 0, response_received = 0

    for i, row in enumerate(table):
        if filename in row[URL_INDEX]:
            request_sent = float(row[TIMESTAMP_INDEX])
            flag = True

            while flag:
                i += 1

                if "responseReceived" in table[i][METHOD_INDEX]:
                    response_received = table[i][TIMESTAMP_INDEX]
                    flag = False

            break

    return response_received - request_sent


def process_page_load_time(table, filename):
    request_sent = 0

    for row in table:
        if filename in row[URL_INDEX]:
            request_sent = float(row[TIMESTAMP_INDEX])
            break

    assert "loadEventFired" in table[-1][METHOD_INDEX]

    page_loaded = float(table[-1][METHOD_INDEX])

    return page_loaded - request_sent


def process_DOM_load_time(table, filename):
    request_sent = 0, dom_loaded = 0

    for row in table:
        if filename in row[URL_INDEX]:
            request_sent = float(row[TIMESTAMP_INDEX])

        if "domContentEventFired" in row[METHOD_INDEX]:
            dom_loaded = row[TIMESTAMP_INDEX]
            break

    return dom_loaded - request_sent


def process_mimetypes(table, filename):
    # Size of each type

    plaintexts = 0
    html = 0
    js_css = 0
    img_others = 0





def preprocess(dir="../rawdata/"):
    data_files = filter(
        lambda x: re.match(".+csv$", x),
        os.listdir(dir))

    header = ["Protocol", "Site", "HandshakeTime", "PageLoadTime",
              "DOMLoadTime", "PlainTexts", "HTML", "JS/CSS",
              "Images/Others", "Domains", "EncodedDataSize", "TotalDataSize"]

    g = open("../statistics.csv", "a")
    g.write(",".join(header) + "\n")

    for filename in data_files:
        f = open(filename, "r")
        _table = f.read().split("\n")
        table = []

        for _t in _table:
            table.append(_t.split(","))

        protocol = "TBD"
        site = filename.split(".")[0]
        handshake_time = process_handshake(table, filename)
        page_load_time = process_page_load_time(table, filename)
        DOM_load_time = process_DOM_load_time(table, filename)
        plaintexts, html, js_css, img_others = \
            process_mimetypes(table, filename)
        domains = process_domains(table)
        datasize_encoded, datasize = process_datasize(table)

        g.write(",".join(
                [
                    str(protocol), str(site), str(handshake_time), str(page_load_time),
                    str(DOM_load_time), str(plaintexts), str(html), str(js_css), str(img_others),
                    str(domains), str(datasize_encoded), str(datasize)
                ]
            ) + "\n"
        )

        f.close()

    g.close()




















