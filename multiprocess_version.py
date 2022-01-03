import jk_pypiorgapi
from datetime import datetime
import re
import requests
import time
from pprint import pprint
import json
import pickle
from multiprocessing import Pool
from pytablewriter import MarkdownTableWriter


# set up autentification github
username = 'edigeze'
token = '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'
repos_url = 'https://api.github.com/user/repos'

# create a re-usable session object with the user creds in-built
gh_session = requests.Session()
gh_session.auth = (username, token)

# list all pypi package
api = jk_pypiorgapi.PyPiOrgAPI()

def grab_package(package):
    jData = api.getPackageInfoJSON(package[1])

    # size of the doc assuming that the doc size is big meaning that the package is important
    doc_size = len(str(jData))

    try:
        amount_of_releases = None
        last_update = datetime.strptime("1900-01-01T01:01:01", "%Y-%m-%dT%H:%M:%S")
        amount_of_releases = len(jData["releases"])
        for rkey, rvalue in jData["releases"].items():
            datetime_object = datetime.strptime(rvalue[0]["upload_time"], "%Y-%m-%dT%H:%M:%S")
            if datetime_object > last_update: last_update = datetime_object
    except:

        pass

    try:
        url = None
        if "github" in jData["info"]["home_page"] or "gitlab" in jData["info"]["home_page"]:
            url = jData["info"]["home_page"]
        elif "github" in jData["info"]["download_url"] or "gitlab" in jData["info"]["download_url"]:
            url = jData["info"]["download_url"]
        # elif "https://git"in jData["info"]["description"]:  # looking for git to include github and gitlab
        #     url=re.search("(?P<url>https?://github.com/[^\s]+)", jData["info"]["description"]).group("url")
        # elif "https://git"in jData["info"]["description"]:
        #     url=re.search("(?P<url>https?://github.com/[^\s]+)", str(jData)).group("url")
        #     print("la tu deconnes")
    except:
        pass

    delta = datetime.now() - last_update

    # connect to stats:
    github_stars = -1  # -1 mean didn't find any repo
    github_last_commit = None
    github_api_timeout = None
    while github_api_timeout is None:
        try:
            if "github" in url and delta.days < 7:  # we check the repo if it's github and if the last release is less than 2 years old (700 days)
                url_github = f"https://api.github.com/repos/{url.split('/')[3]}/{url.split('/')[4]}"
                user_data = gh_session.get(url_github).json()
                github_stars = user_data['stargazers_count']
                github_last_commit = user_data['pushed_at']
            github_api_timeout = True

        except KeyError:
            if 'message' in user_data:
                github_api_timeout = True
            else:
                print("wait for API github timeout finished")
                time.sleep(60)
        except:
            github_api_timeout = True
            pass

    info = {"url": url,
            "Last_update": last_update,
            "Amount_of_releases": amount_of_releases,
            "Doc_size": doc_size,
            "github_stars": github_stars,
            "github_last_commit": github_last_commit
            }
    return package[1],  info

if __name__ == '__main__':

    list_packages = api.listAllPackages()
    list_packages = list_packages[:5000]  # to remove if I want to parse all package
    n = len(list_packages)
    print("Number of packages on pypi.org:", n)
    start_time = time.time()

    pool = Pool()                                              # Create a multiprocessing Pool
    package_info = dict(pool.map(grab_package, list_packages)) # process data_inputs iterable with pool

    print(f'time : {(time.time() - start_time)}')
    package_info = {k: v for k, v in sorted(package_info.items(), key=lambda item: item[1]["github_stars"],reverse=True)}


    # for name, info in package_info.items():
    #     print(name, info)

    with open('src/saved_dictionary.pkl', 'wb') as f:
        pickle.dump(package_info, f)


    value_matrix = []
    for idx , (name, info) in enumerate(package_info.items()):
        print(name, info)
        value_matrix.append([idx,name,info["github_stars"], info['url'] ])
        if len(value_matrix)==100:
            break



    writer = MarkdownTableWriter(
        table_name="top stared packages first 5000",
        headers=["rank", "package", "stars", "url"],
        value_matrix=value_matrix,
    )
    writer.write_table()
    writer.dump("README.md")
