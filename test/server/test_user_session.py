import json
from unittest.mock import MagicMock, patch, ANY

import flask
import pytest

from randovania.network_common.error import InvalidSession
from randovania.server import user_session
from randovania.server.database import User


def test_setup_app():
    user_session.setup_app(MagicMock())


@patch("requests_oauthlib.OAuth2Session.fetch_token", autospec=True)
def test_login_with_discord(mock_fetch_token: MagicMock, clean_database, flask_app):
    # Setup
    sio = MagicMock()
    session = {}
    sio.session.return_value.__enter__.return_value = session
    sio.get_session.return_value = session
    mock_fetch_token.return_value = "access_token"
    sio.fernet_encrypt.encrypt.return_value = b"encrypted"

    discord_user = sio.discord.fetch_user.return_value
    discord_user.id = 1234
    discord_user.name = "A Name"

    # Run
    with flask_app.test_request_context():
        result = user_session.login_with_discord(sio, "code")

    # Assert
    mock_fetch_token.assert_called_once_with(
        ANY,
        "https://discord.com/api/oauth2/token",
        code="code",
        client_secret=sio.app.config["DISCORD_CLIENT_SECRET"],
    )
    user = User.get(User.discord_id == 1234)
    assert user.name == "A Name"

    assert session == {
        "user-id": user.id,
        "discord-access-token": "access_token",
    }
    assert result == {
        "user": user.as_json,
        "sessions": [],
        "encoded_session_b85": b'Wo~0~d2n=PWB',
    }


@patch("randovania.server.user_session._create_client_side_session", autospec=True)
def test_restore_user_session_with_discord(mock_create_session: MagicMock,
                                           flask_app, fernet, clean_database):
    sio = MagicMock()
    sio.fernet_encrypt = fernet

    user: User = User.create(
        id=1234,
        discord_id=5678,
        name="The Name"
    )

    session = {
        "user-id": 1234,
        "discord-access-token": "access-token",
    }
    enc_session = fernet.encrypt(json.dumps(session).encode("utf-8"))

    # Run
    with flask_app.test_request_context():
        flask.request.sid = 7890
        result = user_session.restore_user_session(sio, enc_session, None)

    # Assert
    sio.get_server.return_value.save_session.assert_called_once_with(7890, session)
    mock_create_session.assert_called_once_with(sio, user)
    assert result is mock_create_session.return_value


def test_restore_user_session_invalid_key(flask_app, fernet):
    sio = MagicMock()
    sio.fernet_encrypt = fernet

    with pytest.raises(InvalidSession):
        user_session.restore_user_session(sio, b"", None)
        pass
