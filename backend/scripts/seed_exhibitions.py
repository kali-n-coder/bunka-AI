import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app.db.session import SessionLocal, ensure_database_schema
from app.models.exhibition import Exhibition
from app.models.wait_time import WaitTime


SAMPLES = [
    {"name": "白龍の舞", "description": "光と音で白龍の上昇を表現するステージ展示です。", "category": "展示", "location_name": "体育館ステージ", "duration_minutes": 15, "recommended_for": "演出展示を見たい人、写真を撮りたい人", "cautions": "フラッシュ撮影は控えてください。開演5分前までの入場がおすすめです。", "location_x": 30, "location_y": 30, "wait": 20},
    {"name": "龍の巣カフェ", "description": "白龍モチーフの軽食と飲み物を楽しめる休憩スペースです。", "category": "飲食", "location_name": "本館1階 多目的室", "duration_minutes": 20, "recommended_for": "休憩したい人、飲食を楽しみたい人", "cautions": "混雑時は席の利用時間が制限される場合があります。", "location_x": 25, "location_y": 10, "wait": 5},
    {"name": "受付", "description": "パンフレット配布と総合案内を行います。", "category": "案内", "location_name": "正門入口", "duration_minutes": 5, "recommended_for": "最初に来た人、場所を確認したい人", "cautions": "落とし物や迷子の相談もここで受け付けます。", "location_x": 5, "location_y": 5, "wait": 0},
    {"name": "二階アート回廊", "description": "生徒作品を廊下沿いに展示しています。", "category": "展示", "location_name": "本館2階 廊下", "duration_minutes": 12, "recommended_for": "静かに展示を見たい人", "cautions": "作品には手を触れないでください。", "location_x": 15, "location_y": 35, "wait": 8},
    {"name": "科学実験ラボ", "description": "身近な材料を使った実験を実演します。", "category": "体験", "location_name": "理科室", "duration_minutes": 18, "recommended_for": "体験型企画が好きな人、親子連れ", "cautions": "実験台の薬品や器具にはスタッフの指示なしで触れないでください。", "location_x": 18, "location_y": 26, "wait": 15},
    {"name": "プラネタリウム教室", "description": "教室内に投影した星空を楽しむ上映企画です。", "category": "上映", "location_name": "本館3階 3-B教室", "duration_minutes": 20, "recommended_for": "落ち着いて見たい人、星空が好きな人", "cautions": "上映中の入退室はできるだけ控えてください。", "location_x": 12, "location_y": 40, "wait": 25},
    {"name": "謎解き校内ツアー", "description": "校内を巡りながら謎を解く周遊企画です。", "category": "体験", "location_name": "受付横スタート地点", "duration_minutes": 35, "recommended_for": "友達と一緒に回りたい人", "cautions": "廊下を走らず、周囲に注意して移動してください。", "location_x": 6, "location_y": 8, "wait": 10},
    {"name": "中庭ミニライブ", "description": "有志バンドとダンスチームによる屋外ステージです。", "category": "ステージ", "location_name": "中庭ステージ", "duration_minutes": 25, "recommended_for": "音楽やダンスを楽しみたい人", "cautions": "雨天時は体育館に変更される場合があります。", "location_x": 22, "location_y": 22, "wait": 0},
    {"name": "書道パフォーマンス", "description": "大きな紙に音楽に合わせて文字を書き上げます。", "category": "ステージ", "location_name": "体育館前広場", "duration_minutes": 15, "recommended_for": "迫力ある実演を見たい人", "cautions": "墨が飛ぶ可能性があるため、指定線より前に出ないでください。", "location_x": 28, "location_y": 28, "wait": 5},
    {"name": "写真部ギャラリー", "description": "学校生活や風景をテーマにした写真展示です。", "category": "展示", "location_name": "本館2階 2-C教室", "duration_minutes": 10, "recommended_for": "写真が好きな人、短時間で見たい人", "cautions": "展示写真の無断転載は控えてください。", "location_x": 16, "location_y": 34, "wait": 3},
    {"name": "手作り雑貨マーケット", "description": "生徒が制作した小物やアクセサリーを販売します。", "category": "物販", "location_name": "本館1階 1-A教室", "duration_minutes": 15, "recommended_for": "お土産を探している人", "cautions": "商品数には限りがあります。", "location_x": 11, "location_y": 12, "wait": 12},
    {"name": "お化け屋敷", "description": "教室を使った短時間のお化け屋敷です。", "category": "体験", "location_name": "本館2階 2-D教室", "duration_minutes": 8, "recommended_for": "スリルを楽しみたい人", "cautions": "暗い場所が苦手な方、小さなお子様は注意してください。", "location_x": 19, "location_y": 36, "wait": 40},
    {"name": "ゲームセンター白龍", "description": "射的や輪投げなどのミニゲームを楽しめます。", "category": "体験", "location_name": "本館1階 1-B教室", "duration_minutes": 15, "recommended_for": "短時間で遊びたい人、親子連れ", "cautions": "景品はなくなり次第終了です。", "location_x": 13, "location_y": 13, "wait": 18},
    {"name": "茶道体験", "description": "作法を学びながらお茶を楽しめる体験企画です。", "category": "体験", "location_name": "和室", "duration_minutes": 20, "recommended_for": "落ち着いた体験をしたい人", "cautions": "席数に限りがあるため、待ち時間が発生する場合があります。", "location_x": 9, "location_y": 18, "wait": 22},
    {"name": "美術部ライブペイント", "description": "大きなキャンバスにその場で絵を描き進めます。", "category": "展示", "location_name": "中庭横スペース", "duration_minutes": 10, "recommended_for": "制作過程を見たい人", "cautions": "画材には触れないでください。", "location_x": 21, "location_y": 24, "wait": 4},
    {"name": "古本交換所", "description": "読み終えた本を持ち寄り交換できるコーナーです。", "category": "物販", "location_name": "図書室", "duration_minutes": 10, "recommended_for": "本が好きな人", "cautions": "交換対象外の本もあります。スタッフに確認してください。", "location_x": 10, "location_y": 30, "wait": 2},
    {"name": "白龍クイズ大会", "description": "学校や白龍祭に関するクイズに挑戦できます。", "category": "ステージ", "location_name": "視聴覚室", "duration_minutes": 25, "recommended_for": "みんなで盛り上がりたい人", "cautions": "開始後は途中参加できない場合があります。", "location_x": 17, "location_y": 31, "wait": 7},
    {"name": "休憩ラウンジ", "description": "飲み物を飲みながら休める静かなスペースです。", "category": "休憩", "location_name": "本館1階 会議室", "duration_minutes": 15, "recommended_for": "少し休みたい人、保護者", "cautions": "長時間の席取りは控えてください。", "location_x": 8, "location_y": 11, "wait": 0},
    {"name": "鉄道模型展示", "description": "鉄道模型の走行展示と解説を行います。", "category": "展示", "location_name": "本館3階 3-A教室", "duration_minutes": 12, "recommended_for": "模型や乗り物が好きな人", "cautions": "模型には触れないでください。", "location_x": 14, "location_y": 42, "wait": 9},
    {"name": "ダンスショーケース", "description": "ダンス部による短時間のショーケースです。", "category": "ステージ", "location_name": "体育館ステージ", "duration_minutes": 20, "recommended_for": "ステージ企画を見たい人", "cautions": "開演直前は入口が混雑します。", "location_x": 30, "location_y": 31, "wait": 0},
    {"name": "屋台風焼きそば", "description": "文化祭定番の焼きそばを販売します。", "category": "飲食", "location_name": "中庭テントA", "duration_minutes": 10, "recommended_for": "食事をしたい人", "cautions": "売り切れ次第終了です。", "location_x": 24, "location_y": 23, "wait": 28},
    {"name": "白龍ソーダスタンド", "description": "白龍をイメージした青いソーダを販売します。", "category": "飲食", "location_name": "中庭テントB", "duration_minutes": 5, "recommended_for": "飲み物を買いたい人、写真を撮りたい人", "cautions": "氷の量は選べません。", "location_x": 25, "location_y": 23, "wait": 14},
    {"name": "英語劇ミニステージ", "description": "英語部による短い劇の上演です。", "category": "ステージ", "location_name": "視聴覚室", "duration_minutes": 18, "recommended_for": "演劇や英語に興味がある人", "cautions": "上演中は静かに鑑賞してください。", "location_x": 17, "location_y": 32, "wait": 6},
    {"name": "プログラミング体験", "description": "簡単なゲーム作りを体験できます。", "category": "体験", "location_name": "PC室", "duration_minutes": 25, "recommended_for": "ものづくりやITに興味がある人", "cautions": "端末の台数に限りがあります。", "location_x": 20, "location_y": 38, "wait": 30},
    {"name": "合唱ミニコンサート", "description": "合唱部によるミニコンサートです。", "category": "ステージ", "location_name": "音楽室", "duration_minutes": 20, "recommended_for": "音楽をゆっくり楽しみたい人", "cautions": "演奏中の出入りは控えてください。", "location_x": 7, "location_y": 29, "wait": 0},
    {"name": "防災体験コーナー", "description": "防災グッズや避難行動を学べる体験展示です。", "category": "体験", "location_name": "本館1階 1-C教室", "duration_minutes": 15, "recommended_for": "親子連れ、学び系企画が好きな人", "cautions": "体験器具はスタッフの説明後に使用してください。", "location_x": 14, "location_y": 15, "wait": 6},
    {"name": "制服リユース展示", "description": "制服や学校用品のリユース活動を紹介します。", "category": "展示", "location_name": "本館1階 1-D教室", "duration_minutes": 8, "recommended_for": "学校活動に興味がある人", "cautions": "展示品の持ち帰りはできません。", "location_x": 16, "location_y": 15, "wait": 1},
    {"name": "将棋・ボードゲーム部屋", "description": "将棋やボードゲームを自由に体験できます。", "category": "体験", "location_name": "本館2階 2-A教室", "duration_minutes": 25, "recommended_for": "座って遊びたい人、友達と楽しみたい人", "cautions": "混雑時は1ゲームごとに交代してください。", "location_x": 12, "location_y": 34, "wait": 11},
    {"name": "PTAバザー", "description": "日用品や手作り品を販売するバザーです。", "category": "物販", "location_name": "体育館入口前", "duration_minutes": 12, "recommended_for": "買い物を楽しみたい人、保護者", "cautions": "小銭の用意をおすすめします。", "location_x": 29, "location_y": 27, "wait": 16},
    {"name": "校内スタンプラリー", "description": "校内各所のスタンプを集める周遊企画です。", "category": "体験", "location_name": "受付横スタート地点", "duration_minutes": 30, "recommended_for": "校内を広く回りたい人", "cautions": "階段や廊下では走らないでください。", "location_x": 6, "location_y": 7, "wait": 4},
]


def main():
    ensure_database_schema()
    db = SessionLocal()
    try:
        created = 0
        updated = 0
        for item in SAMPLES:
            exhibition = db.query(Exhibition).filter(Exhibition.name == item["name"]).first()
            payload = {key: value for key, value in item.items() if key != "wait"}
            if not exhibition:
                exhibition = Exhibition(**payload)
                db.add(exhibition)
                db.flush()
                created += 1
            else:
                for key, value in payload.items():
                    setattr(exhibition, key, value)
                updated += 1

            wait_time = db.query(WaitTime).filter(WaitTime.exhibition_id == exhibition.id).first()
            if not wait_time:
                db.add(WaitTime(exhibition_id=exhibition.id, current_wait_minutes=item["wait"]))
        db.commit()
        print(f"Seed completed. Created exhibitions: {created}. Updated exhibitions: {updated}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
