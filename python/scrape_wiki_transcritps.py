from pathlib import Path
from typing import Any

import bs4
import pandas as pd
from bs4 import BeautifulSoup

import requests as req

def get_line_dict(line_text:str) -> dict[str, Any] | None:
    """Returns a dictionary describing the line, used as a row in the dataframe"""
    # at the end of episodes, we don't want to process this


def get_episode_lines(website_content: BeautifulSoup, season:int, episode:int) -> list[dict]:
    rows = []
    if website_content:
        # Creating a BeautifulSoup object and specifying the parser
        S = BeautifulSoup(website_content.content, 'html.parser')
        episode_content = S.find_all('div', class_='mw-parser-output')[0]
        scene_count = 0
        for c in episode_content.children:
            # the lines are stored in paragraph elements
            if c.name == 'p':
                line = c.text.strip('\n \t')
                if '(Credits Roll)' in line:
                    break

                # skip scene descriptions/unknown characters and empty lines
                if len(line) == 0:
                    continue
                elif line[0] == '{':
                    continue
                elif line[0] =='[':
                    continue

                split_line = line.split(":")

                character = split_line[0]
                line_text = ':'.join(split_line[1:])

                line_dict = {
                    'season': season,
                    'episode': episode,
                    'scene': scene_count,
                    'character': character,
                    'line': line_text
                }
                rows.append(line_dict)

            # scene changes are <ul> tags in the middle of the data
            elif c.name == 'ul':
                scene_count += 1
    else:
        return False
    return rows


if __name__ == '__main__':
    OUT_PATH = Path(r"..\data\transcripts.csv")
    episode_list_doc = req.get("https://she-raandtheprincessesofpower.fandom.com/wiki/Episode_Transcript_List")
    list_soup = BeautifulSoup(episode_list_doc.content, 'html.parser')
    count = 0
    main_page = list_soup.find_all('div', class_='mw-parser-output')[0]

    # list of dataframes to combine into the overall CSV at the end
    dataframes = []

    # each season has an ordered list
    for season_num, season in enumerate(main_page.find_all_next('ol'), 1):
        ep_num = 1
        for child in season.children:
            if isinstance(child, bs4.NavigableString):
                continue
            link = next(child.children)

            # Extract the URL from the link
            url = "https://she-raandtheprincessesofpower.fandom.com" + link['href']
            # Fetch the content of the linked page
            linked_page = req.get(url)
            lines = get_episode_lines(linked_page, season_num, ep_num)
            df = pd.DataFrame(lines)
            dataframes.append(df)

            # failed to process
            if not lines:
                print(f"FAILED TO GET EPISODE {link['href']}")
                continue
            ep_num += 1

    dataframe = pd.concat(dataframes, axis=0)

    dataframe.to_csv(OUT_PATH, index=False)