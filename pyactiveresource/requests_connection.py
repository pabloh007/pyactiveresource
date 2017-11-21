"""A connection object to interface with REST services."""

import base64
import logging
import socket
import sys
import six
from six.moves import urllib
from pyactiveresource import formats

class Error(Exception):
    """A general error derived from Exception."""

    def __init__(self, msg=None, url=None, code=None):
        Exception.__init__(self, msg)
        self.url = url
        self.code = code

class ServerError(Error):
    """An error caused by an ActiveResource server."""
    # HTTP error code 5xx (500..599)

    def __init__(self, response=None):
        if response is not None:
            Error.__init__(self, response.msg, response.url, response.code)
        else:
            Error.__init__(self)


class ConnectionError(Error):
    """An error caused by network connection."""

    def __init__(self, response=None, message=None):
        if not response:
            self.response = Response(None, '')
            url = None
        else:
            self.response = Response.from_httpresponse(response)
            url = response.url
        if not message:
            message = str(self.response)

        Error.__init__(self, message, url, self.response.code)

class Response(object):
    """Represents a response from the http server."""

    def __init__(self, code, body, headers=None, msg='', response=None):
        """Initialize a new Response object.

        code, body, headers, msg are retrievable as instance attributes.
        Individual headers can be retrieved using dictionary syntax (i.e.
        response['header'] => value.

        Args:
            code: The HTTP response code returned by the server.
            body: The body of the response.
            headers: A dictionary of HTTP headers.
            msg: The HTTP message (e.g. 200 OK => 'OK').
            response: The original httplib.HTTPResponse (if any).
        """
        self.code = code
        self.msg = msg
        self.body = body
        if headers is None:
            headers = {}
        self.headers = headers
        self.response = response

    def __eq__(self, other):
        if isinstance(other, Response):
            return ((self.code, self.body, self.headers) ==
                    (other.code, other.body, other.headers))
        return False

    def __repr__(self):
        return 'Response(code=%s, body="%s", headers=%s, msg="%s")' % (
            self.code, self.body, self.headers, self.msg)

    def __getitem__(self, key):
        return self.headers[key]

    def get(self, key, value=None):
        return self.headers.get(key, value)

    @classmethod
    def from_httpresponse(cls, response):
        """Create a Response object based on an httplib.HTTPResponse object.

        Args:
            response: An httplib.HTTPResponse object.
        Returns:
            A Response object.
        """
        return cls(response.code, response.read(),
                   dict(response.headers), response.msg, response)


class Connection(object):
    """A connection object to interface with REST services."""

    def __init__(self, site, user=None, password=None, timeout=None,
                 format=formats.JSONFormat):
        """Initialize a new Connection object.

        Args:
            site: The base url for connections (e.g. 'http://foo')
            user: username for basic authentication.
            password: password for basic authentication.
            timeout: socket timeout.
            format: format object for en/decoding resource data.
        """
