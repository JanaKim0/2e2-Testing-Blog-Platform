"""
One class per page of the application.

The tests say *what* a person does; these classes know *how* - which field,
which button, which URL. When the application's markup changes, only this
package changes with it.
"""

from .article_page import ArticlePage
from .base_page import BasePage
from .header import Header
from .login_page import LoginPage
from .people_page import PeoplePage
from .profile_page import ProfilePage
from .register_page import RegisterPage
from .settings_page import SettingsPage

__all__ = [
    "ArticlePage",
    "BasePage",
    "Header",
    "LoginPage",
    "PeoplePage",
    "ProfilePage",
    "RegisterPage",
    "SettingsPage",
]
