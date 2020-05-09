import pathlib
import json
import requests

# TODO: prettify json


class Publish:

    AUTHOR_URL = "https://api.medium.com/v1/me"
    PUB_URL    = "https://api.medium.com/v1/users/{author_id}/publications"
    IMAGE_URL  = "https://api.medium.com/v1/images"
    USER_POST_URL = "POST https://api.medium.com/v1/users/{author_id}/posts"
    PUB_POST_URL = "https://api.medium.com/v1/publications/{pub_id}/posts"
    IMAGE_TYPES = {'png', 'gif', 'jpeg', 'jpg', 'tiff'}
    

    def __init__(self, filename, pub_name, dataframe_image, title, tags, 
                 publish_status, notify_followers, license, canonical_url):
        self.filename = pathlib.Path(filename)
        self.title = title or self.filename.stem
        self.nb_dir = self.filename.resolve().parent
        self.images_dir = self.nb_dir / (self.filename.stem.replace(' ', '_') + '_files')
        self.pub_name = pub_name
        self.publish_status = publish_status
        self.tags = tags
        self.headers = self.get_headers()
        self.author_id = self.get_author_id()
        self.pub_id = self.get_pub_id()
        if dataframe_image:
            self.create_markdown()
        self.load_images_to_medium()
        self.post_to_medium()
        
    def get_headers(self):
        it_path = pathlib.Path.home() / '.jupyter_to_medium' / 'integration_token'
        it = open(it_path).read().splitlines()[0]

        headers = {
            'Host': 'api.medium.com',
            'Authorization': f'Bearer {it}',
            'Accept': 'application/json',
            'Accept-Charset': 'utf-8'
            }
        return headers

    def get_author_id(self):
        r = requests.get(self.AUTHOR_URL, headers=self.headers)
        return r.json()['data']['id']

    def get_pub_id(self):
        if not self.pub_name:
            return ''
        pub_url = self.PUB_URL.format(author_id=self.author_id)
        r = requests.get(pub_url, headers=self.headers)
        data = r.json()['data']
        for d in data:
            if d['name'] == self.pub_name:
                return d['id']
        raise ValueError(f'Publication {self.pub_name} was not found. '
                         f'Here is the data returned {data}')

    def create_markdown(self):
        from dataframe_image import convert
        convert(self.filename, to='md')

    def load_images_to_medium(self):
        all_json = []
        for file in self.images_dir.iterdir():
            extension = file.suffix[1:].lower()
            if extension in self.IMAGE_TYPES:
                name = file.stem
                fileobj = file.open(mode='rb')
                file_payload = {'image': (name, fileobj, f'image/{extension}')}
                r = requests.post(self.IMAGE_URL, headers=self.headers, files=file_payload)
                all_json.append(r.json())
        
        with open('medium_images_data_report.json', 'w') as f:
            json.dump(all_json, f)

    def post_to_medium(self):
        p = self.nb_dir / f'{title}.md'
        md = open(p).read()
        if self.pub_id:
            post_url = self.PUB_POST_URL.format(pub_id=self.pub_id)
        else:
            post_url = self.USER_POST_URL.format(author_id=self.author_id)
        canonical_url = f'https://medium.com/{self.pub_name}/{self.title}'
        
        json_data = {
            "title": title,
            "contentFormat": "markdown",
            "content": md,
            "canonicalUrl": canonical_url,
            "tags": ["python", "data visualization", "matplotlib", "pandas", "data science"],
            "publishStatus": self.publish_status,
            "notifyFollowers": "false"
            }
        self.result = requests.post(post_url, headers=self.headers, json=json_data)
        

def publish(filename, pub_name=None, dataframe_image=True, title=None, 
            tags=None, publish_status='draft', notify_followers='false', 
            license=None, canonical_url=None):
    '''
    Publish a Jupyter Notebook directly to Medium as a blog post.
    '''
    p = Publish(filename, pub_name, dataframe_image, title, tags, 
                publish_status, notify_followers, license, canonical_url)
    return p.result.json()