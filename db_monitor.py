"""
数据库实时监控器
和网站并排打开，操作网站后这里自动刷新显示数据变化
"""
import pg8000
import os
import time

DB_CONFIG = dict(
    user='postgres',
    password='ANGGWXissMcnSCmhDwObuasillUnLQSA',
    host='monorail.proxy.rlwy.net',
    port=38881,
    database='railway'
)

def fetch_all():
    conn = pg8000.connect(**DB_CONFIG)
    cur = conn.cursor()

    result = {}

    cur.execute("SELECT id, username, nickname FROM users ORDER BY id")
    result['users'] = cur.fetchall()

    cur.execute("SELECT id, user_id, LEFT(content, 40), created_at, is_pinned FROM messages ORDER BY id")
    result['messages'] = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM replies")
    result['replies_count'] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM likes")
    result['likes_count'] = cur.fetchone()[0]

    conn.close()
    return result


prev = {}
print("=" * 60)
print("  数据库实时监控器 - 开始监控")
print("  操作网站后，这里自动刷新显示变化")
print("=" * 60)
print()

try:
    while True:
        data = fetch_all()
        changed = data != prev

        if changed:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=" * 60)
            print(f"  🕐 {time.strftime('%H:%M:%S')}  数据库实时状态")
            print("=" * 60)

            print(f"\n  👤 用户 ({len(data['users'])} 人)")
            print("  " + "-" * 40)
            for u in data['users']:
                print(f"    [{u[0]}] {u[1]} ({u[2]})")

            print(f"\n  💬 留言 ({len(data['messages'])} 条)")
            print("  " + "-" * 40)
            for m in data['messages']:
                pin = "📌" if m[4] else "  "
                print(f"    {pin}[{m[0]}] user={m[1]}: {m[2]}...")

            print(f"\n  ↩️ 回复: {data['replies_count']} 条")
            print(f"  ❤️ 点赞: {data['likes_count']} 个")
            print()
            print("=" * 60)
            print("  ⏳ 每 2 秒自动刷新 | Ctrl+C 退出")
            print("=" * 60)

            prev = data
        else:
            print(".", end="", flush=True)

        time.sleep(2)

except KeyboardInterrupt:
    print("\n\n已停止监控。")
