from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urlparse

REQUIRED_FIELDS = [
    '物件名_日本語','物件名_英語','住所_日本語','住所_英語','物件種別','募集区分','取引態様','賃料_円',
    '面積_㎡','間取り','築年月','入居可能日','空室状況','リコー3Dツアー　リンク','入力担当','日英整合'
]

CHOICES = {
    '公開ステータス': ['データ準備中','入力済み','山澤確認済み','鵜飼確認済み','公開承認済み','公開中','募集終了'],
    '優先度': ['高','中','低'],
    '物件種別': ['マンション','戸建','サービスアパートメント','その他'],
    '募集区分': ['賃貸','売買','サービスアパートメント'],
    '取引態様': ['貸主','代理','媒介'],
    '契約形態': ['普通借家','定期借家','その他'],
    '空室状況': ['募集中','申込あり','募集停止','契約済','未確認'],
    '駐車場': ['有','無','要確認'],
    'ペット': ['可','不可','相談','要確認'],
    '日英整合': ['未確認','一致','要修正'],
    '業務確認': ['未確認','承認','差戻し'],
    '技術確認': ['未確認','承認','差戻し'],
    '公開承認': ['未確認','承認','差戻し'],
}

@dataclass(frozen=True)
class Issue:
    severity: str
    field: str
    code: str
    message: str


def _blank(v):
    return v is None or (isinstance(v, str) and not v.strip())


def normalize_property_id(value):
    """Compare Excel numeric IDs and edited text IDs consistently."""
    return "" if _blank(value) else str(value).strip()


def _valid_url(v):
    if _blank(v):
        return False
    try:
        p = urlparse(str(v).strip())
        return p.scheme in {'http','https'} and bool(p.netloc)
    except Exception:
        return False


def validate_property(row: dict, duplicate_ids: set | None = None) -> list[Issue]:
    issues: list[Issue] = []
    pid = normalize_property_id(row.get('物件ID'))
    if _blank(pid):
        issues.append(Issue('ERROR','物件ID','ID_MISSING','物件IDが未入力です。'))
    elif duplicate_ids and pid in duplicate_ids:
        issues.append(Issue('ERROR','物件ID','ID_DUPLICATE','物件IDが重複しています。'))

    for f in REQUIRED_FIELDS:
        if _blank(row.get(f)):
            issues.append(Issue('ERROR',f,'REQUIRED_MISSING',f'{f} はExcelの必須項目判定に含まれています。'))

    for field, allowed in CHOICES.items():
        v = row.get(field)
        if not _blank(v) and v not in allowed:
            issues.append(Issue('ERROR',field,'CHOICE_INVALID',f'{field} の値「{v}」は選択肢にありません。'))

    postal = row.get('郵便番号')
    if not _blank(postal) and not re.fullmatch(r'\d{3}-\d{4}', str(postal).strip()):
        issues.append(Issue('WARN','郵便番号','POSTAL_FORMAT','郵便番号は 123-4567 形式を推奨します。'))

    for field, lo, hi in [('賃料_円',0,100_000_000),('管理費_円',0,100_000_000),('敷金_月',0,24),('礼金_月',0,24),('面積_㎡',0.01,10_000)]:
        v = row.get(field)
        if not _blank(v):
            if not isinstance(v, (int,float)) or isinstance(v, bool):
                issues.append(Issue('ERROR',field,'NUMBER_TYPE',f'{field} は数値で入力してください。'))
            elif not (lo <= v <= hi):
                issues.append(Issue('ERROR',field,'NUMBER_RANGE',f'{field} は {lo}～{hi} の範囲外です。'))

    term = row.get('契約期間_月')
    if not _blank(term) and (not isinstance(term,(int,float)) or isinstance(term,bool)):
        issues.append(Issue('WARN','契約期間_月','TERM_TYPE','契約期間_月は「24カ月」ではなく 24 のような数値を推奨します。'))

    for field in ['画像フォルダURL','間取図URL','リコー3Dツアー　リンク','公開URL']:
        v=row.get(field)
        if not _blank(v) and not _valid_url(v):
            issues.append(Issue('WARN',field,'URL_FORMAT',f'{field} がURL形式ではありません。'))

    for ja,en in [('物件名_日本語','物件名_英語'),('住所_日本語','住所_英語'),('説明_日本語','説明_英語')]:
        if _blank(row.get(ja)) != _blank(row.get(en)):
            issues.append(Issue('WARN',f'{ja}/{en}','JA_EN_PAIR','日本語・英語の片方だけが入力されています。'))

    if row.get('日英整合') == '要修正':
        issues.append(Issue('ERROR','日英整合','JA_EN_MISMATCH','日英整合が「要修正」です。公開停止条件に該当します。'))
    elif row.get('日英整合') == '未確認':
        issues.append(Issue('WARN','日英整合','JA_EN_UNCHECKED','日英整合が未確認です。'))

    for status_field, date_field in [('業務確認','業務確認日'),('技術確認','技術確認日'),('公開承認','公開承認日')]:
        status=row.get(status_field); d=row.get(date_field)
        if status == '承認' and _blank(d):
            issues.append(Issue('WARN',date_field,'APPROVAL_DATE_MISSING',f'{status_field}が承認ですが、{date_field}が未入力です。'))
        if status == '差戻し':
            issues.append(Issue('ERROR',status_field,'APPROVAL_REJECTED',f'{status_field}が差戻しです。'))

    if row.get('公開ステータス') in {'公開承認済み','公開中'}:
        missing=[f for f in ['業務確認','技術確認','公開承認'] if row.get(f) != '承認']
        if missing:
            issues.append(Issue('ERROR','公開ステータス','PUBLIC_WITHOUT_APPROVAL','公開段階ですが3段階承認が完了していません: '+', '.join(missing)))

    if row.get('公開ステータス') == '公開中':
        if _blank(row.get('公開日')):
            issues.append(Issue('ERROR','公開日','PUBLIC_DATE_MISSING','公開中ですが公開日が未入力です。'))
        if not _valid_url(row.get('公開URL')):
            issues.append(Issue('ERROR','公開URL','PUBLIC_URL_MISSING','公開中ですが有効な公開URLがありません。'))

    if row.get('空室状況') in {'募集停止','契約済'} and row.get('公開ステータス') == '公開中':
        issues.append(Issue('ERROR','空室状況','STOP_BUT_PUBLIC','募集停止／契約済なのに公開中です。誤問い合わせ防止のため即時確認が必要です。'))
    return issues


def can_publish(row: dict, issues: list[Issue]) -> bool:
    if any(i.severity == 'ERROR' for i in issues):
        return False
    return all(row.get(f) == '承認' for f in ['業務確認','技術確認','公開承認'])
