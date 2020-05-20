from pathlib import Path
import json
import re
import requests


class Publish:

    AUTHOR_URL = "https://api.medium.com/v1/me"
    PUB_URL    = "https://api.medium.com/v1/users/{author_id}/publications"
    IMAGE_URL  = "https://api.medium.com/v1/images"
    USER_POST_URL = "https://api.medium.com/v1/users/{author_id}/posts"
    PUB_POST_URL = "https://api.medium.com/v1/publications/{pub_id}/posts"
    IMAGE_TYPES = {'png', 'gif', 'jpeg', 'jpg', 'tiff'}
    

    def __init__(self, filename, integration_token, pub_name, dataframe_image, 
                 title, tags, publish_status, notify_followers, license, canonical_url):
        self.filename = Path(filename)
        self.integration_token = self.get_integration_token(integration_token)
        self.pub_name = pub_name
        self.dataframe_image = dataframe_image
        self.title = title or self.filename.stem
        self.tags = tags
        self.publish_status = publish_status
        self.notify_followers = str(notify_followers).lower()
        self.license = license
        self.canonical_url = canonical_url
        self.nb_home = self.filename.parent
        
        self.headers = self.get_headers()
        self.author_id = self.get_author_id()
        self.pub_id = self.get_pub_id()
        self.md, self.image_data_dict = self.create_markdown()
        self.load_images_to_medium()
        self.publish_to_medium()

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
        if self.dataframe_image:
            if self.dataframe_image is True:
                self.dataframe_image = {'filename': self.filename, 'execute': False}
            from dataframe_image._convert import Converter, convert
            import inspect
            arg_spec = inspect.getargspec(convert)
            defaults = dict(zip(arg_spec.args[1:], arg_spec.defaults))
            defaults.update(self.dataframe_image)
            # must convert to markdown
            defaults['to'] = 'md'
            c = Converter(**defaults)
            c.convert()
            md = self.get_markdown(c)
            image_data_dict = self.get_image_data(c)
        else:
            from nbconvert.exporters import MarkdownExporter
            me = MarkdownExporter()
            md, resources = me.from_filename(self.filename)
            image_data_dict = resources['outputs']
            image_data_dict = self.get_md_image_data(md, image_data_dict)
        return md, image_data_dict

    def get_markdown(self, converter):
        fn = converter.final_nb_home / (converter.document_name + '.md')
        return open(fn).read()

    def get_image_data(self, converter):
        image_dir = converter.final_nb_home / converter.image_dir_name
        image_data_dict = {}
        for file in image_dir.iterdir():
            data = open(file, 'rb').read()
            rel_fn = Path(converter.image_dir_name) / file.name
            image_data_dict[str(rel_fn)] = data
        return image_data_dict

    def get_md_image_data(self, md, image_data_dict):
        pat_inline = r'\!\[.*?\]\((.*?\.(?:gif|png|jpg|jpeg|tiff))'
        pat_ref = r'\[.*?\]:\s*(.*?\.(?:gif|png|jpg|jpeg|tiff))'
        inline_files = re.findall(pat_inline, md)
        ref_files = re.findall(pat_ref, md)
        all_files = [file.lower().strip() for file in inline_files + ref_files 
                     if not file.lower().startswith('http')]
        for file in all_files:
            fn = self.nb_home / file
            if fn.exists() and file not in image_data_dict:
                image_data_dict[file] = open(fn, 'rb').read()
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
                new_url = req_json['data']['url']
                # TODO: Find tool to make conversion to HTML links
                self.md = self.md.replace(file.replace(' ', '%20'), new_url)
                all_json.append(req_json)
        
        with open('medium_images_data_report.json', 'w') as f:
            json.dump(all_json, f, indent=4)

        # updated markdown
        new_md_filename = self.filename.stem + '_medium.md'
        with open(self.nb_home / new_md_filename, 'w') as f:
            f.write(self.md)

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
        self.result = requests.post(post_url, headers=self.headers, json=json_data)
        

def publish(filename, integration_token=None, pub_name=None, dataframe_image=False, 
            title=None, tags=None, publish_status='draft', notify_followers=False, 
            license='all-rights-reserved', canonical_url=None):
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

        Otherwise, you can pass the integration token directly as a 
        string to this parameter.
    
    pub_name : str, default `None`
        Name of Medium publication. Not necessary if publishing as a user.
    
    dataframe_image : bool or dict, default `False`
        When False (default), the notebook will be converted to
        markdown in its current state and sent to Medium.

        When True, use the package dataframe_image to convert your 
        notebooks to markdown. This is important if you have pandas
        DataFrames as images, since Medium will just display the raw 
        text otherwise.

        Use a dictionary to supply keyword arguments to the `convert` 
        function from dataframe_image. Below are the available keyword
        arguments and their default values.

        max_rows=30,
        max_cols=10,
        ss_width=1000,
        ss_height=900,
        resize=1,
        chrome_path=None,
        limit=None,
        document_name=None,
        execute=True,
        save_notebook=False,
        output_dir=None,
        image_dir_name=None

        
        Use package dataframe_image to convert the notebook to markdown.
        If you set this as `False`, then you must have your notebook 
        already converted to markdown.
        
        Using dataframe_image converts pandas DataFrames to images, which
        is necessary when publishing to Medium. A new markdown file will 
        be created in the same directory as your notebook along with 
        another direcory named {notebook_name}_files containing all
        the DataFrame images (if you have any).
        
    title : str, default `None`
        Title of the Medium post. Leave as `None` to use the name 
        of the notebook as the title.
    
    tags : list of strings, default `None`
        List of tags to classify the post. Only the first five will be used. 
        Tags longer than 25 characters will be ignored.
    
    publish_status : str, default 'draft'
        The status of the post. Valid values are 'public', 'draft', or 'unlisted'.
    
    notify_followers : bool, default False
        Whether to notify followers that the user has published.
    
    license : str, default 'all-rights-reserved'
        The license of the post. Valid values are 'all-rights-reserved', 'cc-40-by', 
        'cc-40-by-sa', 'cc-40-by-nd', 'cc-40-by-nc', 'cc-40-by-nc-nd', 'cc-40-by-nc-sa', 
        'cc-40-zero', 'public-domain'. The default is 'all-rights-reserved'.
    
    canonical_url : str, default `None`
        A URL of the original home of this content, if it was originally 
        published elsewhere.
    '''
    p = Publish(filename, integration_token, pub_name, dataframe_image, title, 
                tags, publish_status, notify_followers, license, canonical_url)
    return p.result.json()