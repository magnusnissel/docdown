import os
import csv
import requests
import datetime
import time

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DOC_DIR = os.path.join(BASE_DIR, "docs")
LIB_CSV_PATH = os.path.join(BASE_DIR, "libraries.csv")
MIN_AGE = 7  # do not download if last download fewer than MIN_AGE days ago

RTD_URL = "http://media.readthedocs.org/pdf/{lib}/stable/{lib}.pdf"
CRAN_URL = "https://cran.r-project.org/web/packages/{lib}/{lib}.pdf"


def download(url, delay=0, ex_delay=30, max_ex_delay=121,
             ua=None, ref=None, verbose=False):
    if not ua:
        ua = 'Mozilla/5.0 (X11; Linux x86_64)'\
             ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.94'\
             ' Safari/537.36'
    if not ref:
        ref = 'http://www.google.com'
    headers = {'user-agent': ua, 'referer': ref}
    if delay > 0:
        time.sleep(delay)
    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        if verbose:
            print(e)
        if ex_delay < max_ex_delay:
            if verbose:
                print("Trying again in", ex_delay, "secs")
            time.sleep(ex_delay)
            ex_delay = 2 * ex_delay
            download(url, delay, ex_delay)
        else:
            return None
    else:
        return response.content


def grab_docs(r):
    lib = r["LIBRARY"].replace(" ", "").lower().strip()
    if r["SOURCE"] == "other":
        url = r["PDF_URL"]
    elif r["SOURCE"] == "readthedocs":
        url = RTD_URL.format(lib=lib)
    elif r["SOURCE"] == "cran":
        url = CRAN_URL.format(lib=lib)
    else:
        url = ""
    if url:
        print("Downloading documentation for {}".format(r["LIBRARY"]))
        print(url)
        p = os.path.join(DOC_DIR, "{}.pdf".format(lib))
        content = download(url, verbose=True)
        if content:
            with open(p, "wb") as h:
                h.write(content)
            r["LAST_ACCESSED"] = datetime.datetime.now().date()
            return r
        else:
            return r
    else:
        return r


def main():
    try:
        os.makedirs(DOC_DIR)
    except FileExistsError:
        pass
    results = []
    min_date = str(datetime.datetime.now().date() -
                   datetime.timedelta(days=MIN_AGE))
    with open(LIB_CSV_PATH) as h:
        reader = csv.DictReader(h)
        for line in reader:
            if "LAST_ACCESSED" not in line.keys() or not line["LAST_ACCESSED"]:
                line["LAST_ACCESSED"] = "2017-01-01"
            lib = line["LIBRARY"].replace(" ", "").lower().strip()
            p = os.path.join(DOC_DIR, "{}.pdf".format(lib))
            if line["LAST_ACCESSED"] <= min_date or not os.path.exists(p):
                result = grab_docs(line)
                results.append(result)
    if results:
        cols = ["LIBRARY", "SOURCE", "PDF_URL", "LAST_ACCESSED"]
        with open(LIB_CSV_PATH, 'w') as h:
            writer = csv.DictWriter(h, fieldnames=cols, dialect="excel")
            writer.writeheader()
            writer.writerows(results)


if __name__ == "__main__":
    main()
