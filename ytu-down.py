try:
    from bs4 import BeautifulSoup
    import typer
    import requests
    from clint.textui import progress
except ImportError:
    import os
    os.system("pip install bs4 typer requests clint")
    from bs4 import BeautifulSoup
    import typer
    import requests
    from clint.textui import progress

app = typer.Typer()

CREDENTIALS = {
    'email': '',
    'password': '',
    'philmsapp': '',
    # fill above

    'Account': None  # will be filled after login
}

counter = 0


def get_count():
    global counter
    counter += 1
    return counter


def get_video_urls(number: str) -> str:
    """Get video urls from a series url"""
    url = 'https://online.yildiz.edu.tr/ViewOnlineLessonProgramForStudent/Watch'
    form_data = {'Data[No]': number}
    cookies = {
        'ASP.NET_SessionId': CREDENTIALS['Account']['SessionId'],
        'philmsapp': CREDENTIALS['philmsapp']
    }
    r = requests.post(url, data=form_data, cookies=cookies)
    soup = BeautifulSoup(r.json().get('Html'), 'html.parser')
    for a in soup.find_all('a', href=True):
        if 'MP4' in a['href']:
            return a['href']
    return None


def get_section_urls(url: str) -> list:
    """Get section urls from a course url"""
    cookies = {
        'ASP.NET_SessionId': CREDENTIALS['Account']['SessionId'],
        'philmsapp': CREDENTIALS['philmsapp']
    }
    number = url.split('/')[-1]
    url = 'https://online.yildiz.edu.tr/ViewOnlineLessonProgramForStudent/ListAttendance'
    form_data = {'Data[LessonProgramNo]': str(number)}
    r = requests.post(url, data=form_data, cookies=cookies)
    soup = BeautifulSoup(r.text, 'html.parser')
    urls = []
    # btn btn-xs btn-info
    for a in soup.find_all('a', href=True):
        if 'watch' in a['onclick']:
            number = a['onclick'].split("'")[1]
            vidoe_url = get_video_urls(number)
            if vidoe_url:
                urls.append(vidoe_url)
    return urls


def dowload_video(url: str, location: str = '.'):
    r = requests.get(url, stream=True)
    with open(f"{location}/{get_count()}.mp4", 'wb') as f:
        total_length = int(r.headers.get('content-length'))
        for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1):
            if chunk:
                f.write(chunk)
                f.flush()


def save_urls(urls: list):
    with open("urls.txt", "w") as f:
        for url in urls:
            f.write(url + "\n")


def read_urls(source: str) -> list:
    with open(source, "r") as f:
        return f.readlines()


def login():
    url = 'https://online.yildiz.edu.tr/Account/Login'
    form_data = {
        'Data.Mail': CREDENTIALS['email'],
        'Data.Password': CREDENTIALS['password'],
    }
    r = requests.post(url, data=form_data)
    if r.json().get('Message') != 'SRV_GET_ACCOUNT_EXECUTED':
        print('Login failed')
        exit(1)
    CREDENTIALS['Account'] = r.json().get('Account')


@app.command(help="Download video urls to a file")
def get_urls(data: str = 'data.txt'):
    print("Started")
    login()
    urls = []
    for url in read_urls(data):
        urls += get_section_urls(url)
    save_urls(urls)
    print(f"Saved {len(urls)} urls to urls.txt")


@app.command(help="Download video url")
def get_url(url: str):
    print("Started")
    login()
    url = get_section_urls(url)
    print(url)


@app.command(help="Download videos from a file")
def download(location: str = 'urls.txt'):
    print("Started")
    with open(location, "r") as f:
        for url in f.readlines():
            dowload_video(url.strip())
            print(f"Downloaded {url}")
    print("Done")


if __name__ == "__main__":
    app()
