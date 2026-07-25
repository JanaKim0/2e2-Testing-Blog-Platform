# E2E Testing — Blog Platform

End-to-end tests for the [Blog Platform](https://github.com/JanaKim0/Blog-Platform),
written in **Python** with **pytest** and **Playwright**.

Every scenario runs in a real browser against the real application: the actual
Spring Boot API and the actual Angular app, started by the test run itself. There
are no mocks and no stubs anywhere in the suite — if a test passes, a person
could have done the same thing by hand.

## The scenarios

| # | Scenario | What it proves |
|---|----------|----------------|
| 1 | A new visitor registers as `testiranje` | The form creates a real account: the header greets the new user **and** the API confirms the account exists |
| 2 | Signed in, find `admin` and write `hello` to them | Search finds the right person, their profile opens, and the message is stored — not just painted on screen |
| 3 | Signing in with the login field left empty fails | The form rejects it itself and never sends the request; nobody is signed in afterwards |
| 4 | Change your own password while signed in as `testiranje` | The old password stops working and the new one starts, in the API and through the sign-in form |

The four run in the order they are numbered, because scenario 1 creates the
account the others use and scenario 4 changes its password. They are not
*dependent* on that order, though: a fixture seeds the account when it is
missing, so any one of them can be run on its own.

### Two places where the requirements and the application disagreed

Both are worth stating plainly, because a test that quietly redefines its
requirement is worse than no test.

**Scenario 2 asked for a chat. The Blog Platform has none** — no message entity,
no conversation endpoint, no chat page. The only way it lets one person write to
another is a comment. So the scenario keeps every part of the requirement that
exists and is worth testing — sign in, search for `admin`, open their profile,
write `hello` where they will read it — and uses the channel the application
actually offers. The application also ships no `admin` account, so the harness
creates one, with a single published article to write under.

**Scenario 3 asked for a sign-in attempt with the email field left empty, and
the sign-in form has no email field.** It has one box that accepts either a
username or an email address. On that form, "the email was not filled in" *is*
"that box was left empty", which is what the test does.

## Getting Started

### Prerequisites

The suite starts the application under test, so everything the Blog Platform
needs is needed here too:

- **Python 3.11+**
- **Java 17+** — for the Spring Boot backend
- **Node.js 20+** and **npm** — for the Angular frontend

PostgreSQL is **not** required. The backend is started on its embedded H2
profile (see [Isolation](#isolation) below).

The two projects are expected to sit side by side:

```
Projects/
├── Blog Platform/                  the application under test
└── 2e2 Testing Blog Platform/      this repository
```

If yours are somewhere else, point `E2E_APP_ROOT` at the Blog Platform checkout.

### 1. Install the Blog Platform's frontend dependencies

Once, in the application under test — the harness starts its dev server but does
not install for it:

```bash
cd "../Blog Platform/frontend" && npm install
```

### 2. Install the test dependencies

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

On macOS or Linux that last line is `source .venv/bin/activate`.

```bash
pip install -r requirements.txt
```

```bash
playwright install chromium
```

### 3. Run the tests

```bash
pytest
```

That is the whole command. The run starts the backend, starts the frontend,
waits for both, executes the four scenarios and shuts everything down again —
roughly 25 seconds once the backend has been compiled once.

A single scenario:

```bash
pytest e2e/tests/test_02_write_to_admin.py
```

Watch it happen in a visible browser, slowed down:

```bash
pytest --headed --slowmo 500
```

Another browser. The suite is browser-agnostic — nothing in it is
Chromium-specific — but Playwright downloads each engine separately, so install
the one you want first:

```bash
playwright install firefox
```

```bash
pytest --browser firefox
```

### When something fails

Every failing test leaves a full-page screenshot of the moment the assertion
broke in `reports/screenshots/`, and both servers' output is in `logs/`
(`backend.log`, `frontend.log`). Between them, they usually answer "why did the
application disagree?" before you have to reproduce anything by hand.

## Isolation

Two decisions keep a test run from interfering with the machine it runs on, and
from being interfered with.

**The servers come up on ports 18081 and 14300**, not on the 8080 and 4200 a
developer uses by hand. A run must not collide with a session that is already
open — and, worse, must never quietly drive somebody else's build. This was not
hypothetical: the machine this suite was written on already had a Blog Platform
listening on 8081.

**The database is thrown away.** The backend runs on its embedded H2 profile,
pointed at a directory inside this project that is deleted before every run. Two
things follow. Registering the user `testiranje` is repeatable, because the blog
is empty every time — with a shared database, scenario 1 would pass exactly once
and then fail forever with "username is already taken". And a developer's real
PostgreSQL data is never touched by a test run.

## Configuration

Nothing needs configuring for a normal run. Everything below is an escape hatch,
read from the environment.

| Variable | Default | |
|---|---|---|
| `E2E_APP_ROOT` | `../Blog Platform` | where the application under test lives |
| `E2E_BACKEND_PORT` | `18081` | |
| `E2E_FRONTEND_PORT` | `14300` | |
| `E2E_START_SERVERS` | `true` | `false` attaches to servers you started yourself — a much faster debugging loop |
| `E2E_RESET_DATABASE` | `true` | `false` keeps the H2 database between runs |
| `E2E_BACKEND_TIMEOUT` | `240` | seconds to wait for the API to answer |
| `E2E_FRONTEND_TIMEOUT` | `300` | seconds to wait for the dev server to build |
| `E2E_NEW_USERNAME` | `testiranje` | the account scenario 1 registers |
| `E2E_NEW_PASSWORD` | `Testiranje-2024` | |
| `E2E_CHANGED_PASSWORD` | `Testiranje-2025-new` | what scenario 4 changes it to |

For example, to iterate on a test against servers that are already up — in
PowerShell:

```bash
$env:E2E_START_SERVERS = "false"; pytest e2e/tests/test_04_change_password.py
```

or in a POSIX shell:

```bash
E2E_START_SERVERS=false pytest e2e/tests/test_04_change_password.py
```

## Tech Stack

| | |
|---|---|
| Language | Python 3.11 |
| Test runner | pytest 8 |
| Browser automation | Playwright 1.49 (`pytest-playwright`) |
| Browsers | Chromium by default; Firefox and WebKit available |
| HTTP client | `requests` — for seeding and for verifying against the API |
| Pattern | Page Object Model |
| Under test | Angular 22 frontend, Spring Boot 4 API, H2 |

## Architecture

```
2e2 Testing Blog Platform/
├── conftest.py                  every shared fixture: the application,
│                                the API client, the page objects, screenshots
├── pytest.ini                   run configuration
├── requirements.txt
└── e2e/
    ├── config.py                every setting, and its default
    ├── app_runner.py            starts and stops the application under test
    ├── api_client.py            REST calls, for setup and verification only
    ├── pages/                   one class per page of the application
    │   ├── base_page.py         what they all share
    │   ├── header.py            navigation, and "am I signed in?"
    │   ├── register_page.py
    │   ├── login_page.py
    │   ├── people_page.py       the directory and its search
    │   ├── profile_page.py      an author's public page
    │   ├── article_page.py      one article and its comments
    │   └── settings_page.py     three forms, so every locator is scoped
    └── tests/                   one file per scenario, numbered
        ├── test_01_registration.py
        ├── test_02_write_to_admin.py
        ├── test_03_login_without_email.py
        └── test_04_change_password.py
```

Three layers, and the boundaries between them are the point.

**`e2e/tests/` says what a person does.** A scenario reads as prose — open the
page, search for admin, write the comment — and contains no selectors at all. It
is the layer somebody who does not know the application can still review.

**`e2e/pages/` knows what the application looks like.** Which field, which
button, which URL. When the markup changes, this is the only layer that changes
with it. Fields are addressed through their **labels** wherever the markup
allows, so a renamed CSS class does not break the suite while a renamed label —
something a user would actually notice — does.

**`conftest.py` and `e2e/app_runner.py` own the environment.** Starting servers,
waiting for them, seeding, cleaning up. No test knows a port number.

### Decisions worth explaining

**Preconditions are seeded over REST; only the behaviour under test goes through
the browser.** Creating the `admin` account and its article is setup, not a
scenario. Driving setup through forms would double the runtime and, worse, would
mean one broken registration page failed three unrelated tests instead of one.

**"Am I signed in?" is asked of the header, never of browser storage.** The
header shows *Sign out* to a signed-in visitor and *Sign in* to everybody else,
so asking it is asking the application. A test that read the JWT out of
`localStorage` would pass on a build where signing in stored a token and rendered
nothing.

**Every scenario verifies against the API as well as the page.** The browser can
be convinced by a form that succeeded locally and persisted nothing. So scenario
1 asks the API whether the account exists, scenario 2 whether the comment is
stored, and scenario 4 whether the old password has genuinely stopped working.

**Scenario 3 asserts that no request was sent, and then proves that assertion
could have failed.** "The form rejected this itself" is the interesting claim,
and it is worthless if a request would not have been noticed either. So the test
fills the field in, submits again, and requires *that* attempt to reach the
server. Without the control step, the assertion would pass against a listener
that saw nothing at all.

**Waits are for conditions, never for time.** `wait_for_url`, `wait_for`,
Playwright's auto-waiting assertions. There is no `sleep` anywhere in the tests or
the page objects, which is why the suite does not get slower on a fast machine or
flaky on a loaded one. The one exception is the harness, which pauses two seconds
between polls while waiting for a server to start — there is nothing there to
wait *on* until the port answers.

**Each test gets its own browser context.** No cookie and no token survives from
one scenario to the next, so a test cannot pass because of something an earlier
one left behind.

### Found along the way

The username field on the settings page has a `<label>` with no `for` attribute
that does not wrap its input, so the two are not associated. The test locates it
through its wrapper instead — and a screen reader has exactly the same problem,
which makes it a small accessibility gap in the application rather than an
awkwardness in the suite. Noted in `e2e/pages/settings_page.py`, where the
workaround lives.

## Credits

Written by **Jana Kim**.

Developed together with **Claude** (Anthropic) as a pair-programming partner.
The scope was worked out before any code was written — including finding that
scenario 2's chat did not exist and agreeing what to test instead — and the suite
was then built stage by stage, each stage a single commit whose tests were run
before it was made.
