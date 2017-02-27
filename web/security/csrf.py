# encoding: utf-8

import hashlib, hmac
from os import urandom
from binascii import hexlify, unhexlify

from web.security.predicate import Predicate

try:
    from hmac import compare_digest
except ImportError:
    def compare_digest(a, b):
        return a == b


log = __import__('logging').getLogger(__name__)


class CSRFError(ValueError):
	pass


class CSRFPasses(Predicate):
    def __init__(self, *predicates):
        pass
    
    def __call__(self, context):
        if context.request.method in ('POST', 'PUT', 'DELETE'):
            # Probably need to make the var name configurable somehow
            token = context.request.POST['csrftoken']
            return context.csrf(token)
        return True


class CSRFToken(object):
    def __init__(self, value=None):
        """
        `value` is expected to be hexlified bytes data
        """
        if value:
            self.parse(value)
        else:
            self.generate()
        
    def parse(self, value):
        self.value = value
        if hasattr(self.value, 'encode'):
            self.value = self.value.encode('ascii')
    
    def generate(self):
        self.value = hexlify(urandom(32))
    
    def __str__(self):
        return self.value.decode('ascii')
    
    def __bytes__(self):
        return unhexlify(self.value)

class SignedCSRFToken(CSRFToken):
    def __init__(self, value=None, secret=None):
        self._secret = secret.encode('ascii') if hasattr(secret, 'encode') else secret
        self._secret = None
        
        super(SignedCSRFToken, self).__init__(value)
    
    def parse(self, value):
        super(SignedCSRFToken, self).parse(value[:64])
        
        self._secret = value[64:]
        if hasattr(self._secret, 'encode'):
            self._secret = self._secret.encode('ascii')
        
        if not self.valid:
            raise CSRFError("Invalid signed csrf token.")
    
    @property
    def signed(self):
        return self.value + self.signature
    
    @property
    def signature(self):
        if not self._secret:
            self._secret = hmac.new(
                    self._secret,
                    unhexlify(self.value),
                    hashlib.sha256
                ).hexdigest()
                
            if hasattr(self._secret, 'encode'):
                self._secret = self._secret.encode('ascii')
            
        return self._secret
    
    @property
    def valid(self):
        if not self._secret:
            raise CSRFError("No signature present.")
            return False
            
        challenge = hmac.new(
                self._secret,
                unhexlify(self.value),
                hashlib.sha256
            ).hexdigest()
            
        if hasattr(challenge, 'encode'):
            challenge = challenge.encode('ascii')
            
        result = compare_digest(challenge, self.signature)
        
        if not result:
            raise CSRFError("Invalid Signature: ", repr(challenge), repr(self._secret))
            return False
            
        return True
