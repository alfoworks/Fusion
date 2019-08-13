import requests
from urllib import parse

import six

proxy_url = "http://www.ipv6proxy.net/go.php?u="


def get_url(url):
    return proxy_url + parse.quote_plus(url)


class DotList(list):
    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for elem in self:
            if type(elem) == dict:
                self[self.index(elem)] = DotDict(elem)
            elif type(elem) == list:
                self[self.index(elem)] = DotList(elem)


class DotDict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self:
            value = self[key]
            if type(value) == dict:
                self[key] = DotDict(value)
            elif type(value) == list:
                self[key] = DotList(value)


class ApiError(Exception):
    code: int
    description: str

    def __init__(self, error_code, description):
        self.code = error_code
        self.description = description

    def __str__(self):
        return "[%s] %s" % (self.code, self.description)


class TGBot:
    token = None

    def __init__(self, token):
        self.token = token

    def method(self, method, **kwargs):
        url = get_url("https://api.telegram.org/bot%s/%s" % (self.token, method))
        driver = requests.get
        driver_kwargs = {}
        if kwargs:
            driver = requests.post
            driver_kwargs["json"] = kwargs
        response = driver(url, **driver_kwargs)
        json = response.json()
        if not json["ok"]:
            raise ApiError(json["error_code"], json["description"])
        return DotDict(json["result"])

    def get_api(self):
        return TGApi(self)


class TGLongpoll:
    tg = None
    offset = None

    def __init__(self, tg):
        self.tg = tg.get_api()

    def check(self, **kwargs):
        if self.offset is not None:
            kwargs["offset"] = self.offset
        res = self.tg.getUpdates(**kwargs)
        updates: list = res.json()
        last = updates[-1]
        self.offset = last["update_id"] + 1
        return updates


class TGApi:
    tg = None
    method = None

    def __init__(self, tg, method=None):
        self.tg = tg
        self.method = method

    def __getattr__(self, method):
        return TGApi(
            self.tg,
            (self.method + '.' if self.method else '') + method
        )

    def __call__(self, **kwargs):
        for k, v in six.iteritems(kwargs):
            if isinstance(v, (list, tuple)):
                kwargs[k] = ','.join(str(x) for x in v)

        return self.tg.method(self.method, **kwargs)
