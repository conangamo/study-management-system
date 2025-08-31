"""
Custom middleware for session management - Simplified for personal use
"""
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.contrib.sessions.backends.db import SessionStore
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SimpleSessionMiddleware(MiddlewareMixin):
    """
    Simple session middleware for personal use
    - Uses standard Django session management
    - No complex session separation needed
    """
    
    def process_request(self, request):
        # Use standard Django session management
        session_key = request.COOKIES.get('sessionid')
        
        if session_key:
            try:
                # Verify session exists and is valid
                session = Session.objects.get(session_key=session_key)
                if session.expire_date and session.expire_date > timezone.now():
                    # Create session store with existing key
                    request.session = SessionStore(session_key=session_key)
                    logger.debug(f"Using existing session: {session_key}")
                else:
                    # Session expired, delete it
                    session.delete()
                    logger.debug(f"Expired session deleted: {session_key}")
                    # Create new session
                    request.session = SessionStore()
            except Session.DoesNotExist:
                # Session doesn't exist, create new one
                request.session = SessionStore()
                logger.debug(f"Session not found, creating new session")
        else:
            # No session cookie, create new session
            request.session = SessionStore()
            logger.debug(f"No session cookie, creating new session")
    
    def process_response(self, request, response):
        # Set session cookie if session exists
        if hasattr(request, 'session') and request.session.session_key:
            response.set_cookie(
                'sessionid',
                request.session.session_key,
                max_age=getattr(settings, 'SESSION_COOKIE_AGE', 86400),
                httponly=True,
                samesite='Lax',
                path='/'
            )
            logger.debug(f"Set session cookie: {request.session.session_key}")
        
        return response


# Keep legacy middleware classes for backward compatibility but they won't be used
class MultipleSessionMiddleware(MiddlewareMixin):
    """Legacy middleware - not used"""
    pass


class CustomSessionMiddleware(SessionMiddleware):
    """Legacy middleware - not used"""
    pass


class CustomAuthMiddleware(AuthenticationMiddleware):
    """Legacy middleware - not used"""
    pass


class SessionConflictMiddleware(MiddlewareMixin):
    """Legacy middleware - not used"""
    pass


class SessionCleanupMiddleware(MiddlewareMixin):
    """Legacy middleware - not used"""
    pass


class SessionSecurityMiddleware(MiddlewareMixin):
    """Legacy middleware - not used"""
    pass


class SessionDomainMiddleware(MiddlewareMixin):
    """Legacy middleware - not used"""
    pass


class RobustSessionSeparationMiddleware(MiddlewareMixin):
    """Legacy middleware - not used"""
    pass 