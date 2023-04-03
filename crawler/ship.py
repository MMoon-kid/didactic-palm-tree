import requests, bs4, multiprocessing as mp
import sys, time, dataclasses, tqdm
from crawler.parse_data import *
sys.setrecursionlimit(1000000)

URLQuery = (
    "https://www.yachtworld.com/boats-for-sale/condition-used/type-sail/?keyword="
)
urlHead = "https://www.yachtworld.com/yacht/"


@dataclasses.dataclass
class ShipInfo:
    draft: float = None
    beam: float = None
    room: float = None
    material: str = None


def parseYacht(url: str, record: ShipInfo) -> None:
    while (html := requests.get(url)).status_code != 200:
        time.sleep(0.1)
    soup = bs4.BeautifulSoup(html.text, "html.parser")
    if record.material is None:
        try:
            div = soup.find("div", class_="detail-data-table details")
            for tr in div.findAll("tr", class_="datatable-item"):
                if "Hull Material" in tr.text:
                    record.material = tr.find("td", class_="datatable-value").string
                    break
        except Exception as e:
            print(url, '\n', "material", e.args)
    div = soup.find("div", class_="detail-data-table measurements")
    if record.room is None:
        try:
            for div_ in div.findAll("div", class_="datatable-category"):
                if div_.h3.string == "Accommodations":
                    record.room = sum(
                        float(td.string)
                        for td in div_.findAll("td", class_="datatable-value")
                    )
                    break
        except Exception as e:
            print(url, '\n', "room", e.args)
    try:
        for tr in div.findAll("tr", class_="datatable-item"):
            if record.beam is None and "Beam" in tr.text:
                record.beam = float(
                    tr.find("td", class_="datatable-value").string.removesuffix("ft")
                )
            if record.draft is None and "Max Draft" in tr.text:
                record.draft = float(
                    tr.find("td", class_="datatable-value").string.removesuffix("ft")
                )
    except Exception as e:
        print(url, '\n', "material", e.args)


def searchYacht(word: str, bar: tqdm.tqdm = tqdm.tqdm()):
    bar.set_description(f"Process[{-bar.pos}]{word:40}")
    while (html := requests.get(URLQuery + word)).status_code != 200:
        time.sleep(0.1)
    soup = bs4.BeautifulSoup(html.text, "html.parser")
    ret = ShipInfo()
    for div in soup.find("div", class_="listings-container").findAll('a'):
        bar.set_description(
            f"Process[{-bar.pos}]{div['href'].removeprefix(urlHead):40}"
        )
        parseYacht(div["href"], ret)
        if all(i is not None for i in (ret.beam, ret.draft, ret.material, ret.room)):
            return ret
    return ret


def searchYachts(pid: int, words: list[str]):
    bar = tqdm.tqdm(words, position=pid)
    return [searchYacht(i, bar) for i in bar]


if __name__ == "__main__":
    processNumber = 6
    s_ = splitBy(s, processNumber)
    p = mp.Pool(processNumber, initializer=tqdm.tqdm.set_lock, initargs=(mp.RLock(),))
    results = [p.apply_async(searchYachts, args=(i, s_i)) for i, s_i in enumerate(s_)]
    p.close()
    p.join()
    result = sum((i.get() for i in results), [])
    with open("other_data.csv", "w") as f:
        for info in result:
            f.write(f"{info.beam} {info.draft} {info.material} {info.room}\n")


"""
'Length Overall'
'Beam'
'Fresh Water Tank'
'Fuel Tank'
'Holding Tank'
"""


"""
{'Cabins': 22, 'Max Speed': 18, 'Max Bridge Clearance': 21, 'Single Berths': 21, 'Windlass': 21, 
'Length Overall': 22, 
'Heads': 22, 'Electrical Circuit': 19, 'Double Berths': 21, 'Liferaft Capacity': 12, 
'Fuel Tank': 22, 
'Max Draft': 22, 
'Length at Waterline': 22, 
'Beam': 22, 
'Holding Tank': 22, 'Cabin Headroom': 19, 'Cruising Speed': 20, 'Length on Deck': 16, 
'Fresh Water Tank': 22, 
'Dry Weight': 22, 'Range': 9, 'Twin Berths': 11, 'Seating Capacity': 7, 'Deadrise At Transom': 3, 'Freeboard': 3}"""
