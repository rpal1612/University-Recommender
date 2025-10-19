import json
import importlib
srv = importlib.import_module('server.server')


def main():
    app = srv.app
    client = app.test_client()
    payload = {
        "user_prefs": {
            "preferred_countries": ["UK"],
            "program_duration": "1 Year",
            "budget_usd": 40000,
            "target_tier": "Elite",
            "focus": "Research",
            "research_focused": True,
            "internship_ok": True,
            "work_visa": True
        }
    }
    resp = client.post('/api/recommend', json=payload)
    print('Status:', resp.status_code)
    data = resp.get_json()
    print('Meta:', json.dumps(data.get('meta', {}), indent=2))
    top5 = data.get('top5', [])
    print('Top3:')
    for item in top5[:3]:
        print('-', item['university_name'], item['country'], 'score=', round(item['total_score'], 4))


if __name__ == '__main__':
    main()
