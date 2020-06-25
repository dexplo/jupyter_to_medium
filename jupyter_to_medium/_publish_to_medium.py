from pathlib import Path
import json
import re
import urllib.parse

import requests
import nbformat
from nbconvert.exporters import MarkdownExporter

from ._preprocesors import MarkdownPreprocessor, NoExecuteDataFramePreprocessor
from ._screenshot import Screenshot


class Publish:

    AUTHOR_URL = "https://api.medium.com/v1/me"
    PUB_URL    = "https://api.medium.com/v1/users/{author_id}/publications"
    IMAGE_URL  = "https://api.medium.com/v1/images"
    USER_POST_URL = "https://api.medium.com/v1/users/{author_id}/posts"
    PUB_POST_URL = "https://api.medium.com/v1/publications/{pub_id}/posts"
    IMAGE_TYPES = {'png', 'gif', 'jpeg', 'jpg', 'tiff'}
    

    def __init__(self, filename, integration_token, pub_name, title, tags, 
                 publish_status, notify_followers, license, canonical_url,
                 chrome_path, save_markdown, table_conversion):
        self.filename = Path(filename)
        self.img_data_json = self.filename.stem + '_image_data.json'
        self.integration_token = self.get_integration_token(integration_token)
        self.pub_name = pub_name
        self.title = title or self.filename.stem
        self.tags = tags or []
        self.publish_status = publish_status
        self.notify_followers = str(notify_followers).lower()
        self.license = license
        self.canonical_url = canonical_url
        self.chrome_path = chrome_path
        self.save_markdown = save_markdown
        self.table_conversion = table_conversion
        self.nb_home = self.filename.parent
        self.image_dir_name = self.title + '_files'
        self.resources = self.get_resources()
        self.nb = self.get_notebook()
        self.headers = self.get_headers()
        self.validate_args()


    def validate_args(self):
        if self.publish_status != 'draft':
            raise ValueError('Only "draft" is allowed as a publish status for now')

        licenses = ['all-rights-reserved', 'cc-40-by', 'cc-40-by-sa', 'cc-40-by-nd', 
                    'cc-40-by-nc', 'cc-40-by-nc-nd', 'cc-40-by-nc-sa', 'cc-40-zero', 
                    'public-domain']
        if self.license not in licenses:
            raise ValueError('License must be one of', licenses)

        if not isinstance(self.tags, list):
            raise TypeError('Must use a list of strings for the tags and not', self.tags)

        if self.table_conversion not in ('chrome', 'matplotlib'):
            raise ValueError('`table_version` must be either "chrome" or "matplotlib"')
        
    def get_resources(self):
        resources = {'metadata': {'path': str(self.nb_home), 
                                  'name': self.title},
                     'output_files_dir': self.image_dir_name}
        return resources

    def get_notebook(self):
        with open(self.filename) as f:
            nb = nbformat.read(f, as_version=4)
        return nb

    def get_integration_token(self, it):
        if not it:
            it_path = Path.home() / '.jupyter_to_medium' / 'integration_token'
            it = open(it_path).read().splitlines()[0]
        return it

    def get_headers(self):
        headers = {
            'Host': 'api.medium.com',
            'Authorization': f'Bearer {self.integration_token}',
            'Accept': 'application/json',
            'Accept-Charset': 'utf-8'
            }
        return headers

    def get_author_id(self):
        r = requests.get(self.AUTHOR_URL, headers=self.headers)
        try:
            return r.json()['data']['id']
        except KeyError:
            raise ValueError('Problem authenticating author: \n' + r.text)

    def get_pub_id(self):
        if not self.pub_name:
            return ''
        pub_url = self.PUB_URL.format(author_id=self.author_id)
        r = requests.get(pub_url, headers=self.headers)
        try:
            data = r.json()['data']
        except KeyError:
            raise ValueError('Problem getting publication: \n' + r.text)

        for d in data:
            if d['name'] == self.pub_name:
                return d['id']
        raise ValueError(f'Publication {self.pub_name} was not found.\n'
                         f'Here is the publication data returned from Medium\n\n{data}')

    def create_markdown(self):
        output_dir = self.nb_home / self.image_dir_name
        if not output_dir.exists():
            output_dir.mkdir()
        mp = MarkdownPreprocessor(output_dir=output_dir,
                                  image_dir_name=Path(self.image_dir_name))
        self.nb, self.resources = mp.preprocess(self.nb, self.resources)

        no_ex_pp = NoExecuteDataFramePreprocessor()
        if self.table_conversion == 'chrome':
            converter = Screenshot(max_rows=30, max_cols=10, ss_width=1400, 
                                   ss_height=900, resize=1, chrome_path=None).run
        else:
            from ._matplotlib_table import mpl_make_table as converter
        self.resources['converter'] = converter
        self.nb, self.resources = no_ex_pp.preprocess(self.nb, self.resources)

        me = MarkdownExporter()
        md, self.resources = me.from_notebook_node(self.nb, self.resources)
        image_data_dict = self.resources['outputs']
        self.write_output_image_data(image_data_dict)
        image_data_dict = self.get_image_data(image_data_dict)
        return md, image_data_dict

    def write_output_image_data(self, image_data_dict):
        if self.save_markdown:
            image_dir = self.nb_home / self.image_dir_name
            for file, image_data in image_data_dict.items():
                fn = image_dir / Path(file).name
                with open(fn, 'wb') as f:
                    f.write(image_data)

    def get_image_data(self, image_data_dict):
        image_dir = self.nb_home / self.image_dir_name
        for file in image_dir.iterdir():
            data = open(file, 'rb').read()
            rel_fn = Path(self.image_dir_name) / file.name
            image_data_dict[str(rel_fn)] = data
        return image_data_dict

    def load_images_to_medium(self):
        all_json = []
        for file, data in self.image_data_dict.items():
            fp = Path(file)
            extension = fp.suffix[1:].lower()
            if extension in self.IMAGE_TYPES:
                print('loading image to medium')
                name = fp.stem
                file_payload = {'image': (name, data, f'image/{extension}')}
                r = requests.post(self.IMAGE_URL, headers=self.headers, files=file_payload)
                req_json = r.json()
                try:
                    new_url = req_json['data']['url']
                except KeyError:
                    raise ValueError('Problem loading images: ' + r.text)
                self.md = self.md.replace(urllib.parse.quote(fp.as_posix()), new_url)
                all_json.append(req_json)
        
        if self.save_markdown:
            with open(self.nb_home / self.img_data_json, 'w') as f:
                json.dump(all_json, f, indent=4)

    def save_or_delete(self):
        # save markdown and add extra image files
        # or delete images
        if self.save_markdown:
            new_md_filename = self.filename.stem + '_medium.md'
            with open(self.nb_home / new_md_filename, 'w') as f:
                f.write(self.md)
        else:
            image_dir = self.nb_home / self.image_dir_name
            for file in image_dir.iterdir():
                file.unlink()
            image_dir.rmdir()

    def publish_to_medium(self):
        if self.pub_id:
            post_url = self.PUB_POST_URL.format(pub_id=self.pub_id)
        else:
            post_url = self.USER_POST_URL.format(author_id=self.author_id)
        
        json_data = {
            'title': self.title,
            'contentFormat': 'markdown',
            'content': self.md,
            'license': self.license,
            'publishStatus': self.publish_status,
            'notifyFollowers': self.notify_followers
            }
        if self.canonical_url:
            json_data['canonicalUrl'] = self.canonical_url
        if self.tags:
            json_data['tags'] = self.tags
        
        req = requests.post(post_url, headers=self.headers, json=json_data)
        try:
            self.result = req.json()
        except Exception as e:
            raise ValueError('Problem with posting:\n' + req.text)

    def print_results(self):
        data = self.result
        success = 'data' in data and 'url' in data['data']
        print('\n\n')
        if not success:
            print('Failed to post to Medium. See returned message below')
            print('----------------------------------------------------')
            print(data)
        else:
            print('Successfully posted to Medium!!!')
            print('--------------------------------')
            for k, v in data['data'].items():
                print(f'{k:20}{v}')

    def main(self):
        self.author_id = self.get_author_id()
        self.pub_id = self.get_pub_id()
        self.md, self.image_data_dict = self.create_markdown()
        self.load_images_to_medium()
        self.save_or_delete()
        self.publish_to_medium()
        self.print_results()
        

def publish(filename, integration_token=None, pub_name=None, title=None, 
            tags=None, publish_status='draft', notify_followers=False, 
            license='all-rights-reserved', canonical_url=None, chrome_path=None,
            save_markdown=False, table_conversion='chrome'):
    '''
    Publish a Jupyter Notebook directly to Medium as a blog post.

    Parameters
    ----------
    filename : str 
        Location of Jupyter Notebook to publish to Medium.

    integration_token : str, default None
        When `None`, the integration token must be stored in a file
        located in the users home directory at 
        '.jupyter_to_medium/integration_token'. You'll need to create 
        this directory and file first and paste your token there.

        Otherwise, pass the integration token directly as a string.

        Learn how to get an integration token from Medium.
        https://github.com/Medium/medium-api-docs
    
    pub_name : str, default `None`
        Name of Medium publication. Not necessary if publishing as a user.
        
    title : str, default `None`
        This title is used for SEO and when rendering the post as a listing, 
        but will not appear in the actual post. Use the first cell of the 
        notebook with an H1 markdown header for the title. 
        i.e. # My Actual Blog Post Title 
    
        Leave as `None` to use the filename as this title
    
    tags : list of strings, default `None`
        List of tags to classify the post. Only the first five will be used. 
        Tags longer than 25 characters will be ignored.
    
    publish_status : str, default 'draft'
        The status of the post. Valid values are 'public', 'draft', or 'unlisted'.
        Only draft will be allowed for now. Finalize publication on Medium.
    
    notify_followers : bool, default `False`
        Whether to notify followers that the user has published.
    
    license : str, default 'all-rights-reserved'
        The license of the post. Valid values are 'all-rights-reserved', 'cc-40-by', 
        'cc-40-by-sa', 'cc-40-by-nd', 'cc-40-by-nc', 'cc-40-by-nc-nd', 'cc-40-by-nc-sa', 
        'cc-40-zero', 'public-domain'. The default is 'all-rights-reserved'.
    
    canonical_url : str, default `None`
        A URL of the original home of this content, if it was originally 
        published elsewhere.

    chrome_path : str, default `None`
        Path to your machine's chrome executable. By default, it is 
        automatically found. Use this when chrome is not automatically found.

    save_markdown : bool, default `False`
        Whether or not to save the markdown and corresponding image files. They 
        will be placed in the same folder containing the notebook. The images will be
        in a folder with _files appended to it.

    table_conversion : 'chrome' or 'matplotlib', default 'chrome'
        Medium does not render tables correctly such as pandas DataFrame.
        As a workaround, images of the tables will be produced in their place.
        When 'chrome', a screenshot using the Chrome web browser will be used.
        When 'matplotlib', the matplotlib table function will be used to
        produce the table
        
    '''
    p = Publish(filename, integration_token, pub_name, title, tags, 
                publish_status, notify_followers, license, canonical_url,
                chrome_path, save_markdown, table_conversion)
    p.main()
    return p.result