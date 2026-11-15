import html
import json
import os
import urllib.request

LOGIN = os.environ.get("LOGIN", "shrutisangh")
TOKEN = os.environ["GITHUB_TOKEN"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 6, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar { totalContributions }
    }
  }
}
"""


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": "bearer " + TOKEN, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)["data"]


user = gql(QUERY, {"login": LOGIN})["user"]
name = user["name"] or LOGIN
repos = user["repositories"]
cc = user["contributionsCollection"]
stars = sum(n["stargazerCount"] for n in repos["nodes"])

langs = {}
for n in repos["nodes"]:
    for e in n["languages"]["edges"]:
        langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:5]
total = sum(v for _, v in top) or 1

BG, BORDER, TITLE, TEXT, ACCENT = "#fdf3e3", "#e8c9a0", "#b5532a", "#4a3426", "#e08a3c"
FONT = "font-family=\"Segoe UI, Ubuntu, Helvetica, Arial, sans-serif\""
BARS = ["#d9773d", "#e8927c", "#3a8a9a", "#e9b872", "#b5532a"]

rows = [
    ("Contributions (last year)", cc["contributionCalendar"]["totalContributions"]),
    ("Commits", cc["totalCommitContributions"]),
    ("Pull requests", cc["totalPullRequestContributions"]),
    ("Issues", cc["totalIssueContributions"]),
    ("Public repositories", repos["totalCount"]),
    ("Stars earned", stars),
]

stats = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="190" viewBox="0 0 420 190" {FONT}>',
    f'<rect x="0.5" y="0.5" width="419" height="189" rx="10" fill="{BG}" stroke="{BORDER}"/>',
    f'<text x="24" y="36" font-size="18" font-weight="700" fill="{TITLE}">{html.escape(name)}\'s GitHub Stats</text>',
]
for i, (label, val) in enumerate(rows):
    y = 70 + i * 20
    stats.append(f'<circle cx="30" cy="{y - 4}" r="3.5" fill="{ACCENT}"/>')
    stats.append(f'<text x="42" y="{y}" font-size="14" fill="{TEXT}">{html.escape(label)}</text>')
    stats.append(f'<text x="396" y="{y}" font-size="14" font-weight="700" text-anchor="end" fill="{TEXT}">{val}</text>')
stats.append("</svg>")

lang = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="190" viewBox="0 0 420 190" {FONT}>',
    f'<rect x="0.5" y="0.5" width="419" height="189" rx="10" fill="{BG}" stroke="{BORDER}"/>',
    f'<text x="24" y="36" font-size="18" font-weight="700" fill="{TITLE}">Most Used Languages</text>',
]
if not top:
    lang.append(f'<text x="24" y="90" font-size="14" fill="{TEXT}">No language data yet</text>')
for i, (n, size) in enumerate(top):
    y = 70 + i * 24
    pct = size / total
    lang.append(f'<text x="24" y="{y}" font-size="13" fill="{TEXT}">{html.escape(n)}</text>')
    lang.append(f'<rect x="150" y="{y - 10}" width="200" height="10" rx="5" fill="#f0dcc0"/>')
    lang.append(f'<rect x="150" y="{y - 10}" width="{max(6, round(200 * pct))}" height="10" rx="5" fill="{BARS[i % len(BARS)]}"/>')
    lang.append(f'<text x="396" y="{y}" font-size="13" text-anchor="end" fill="{TEXT}">{pct * 100:.1f}%</text>')
lang.append("</svg>")

os.makedirs("cards", exist_ok=True)
open("cards/stats.svg", "w").write("\n".join(stats))
open("cards/languages.svg", "w").write("\n".join(lang))
print("cards written")
