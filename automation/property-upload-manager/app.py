from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from validator import validate_property, can_publish
from workbook_io import load_master, save_updates_preserving_validations

EDITABLE_FIELDS = ['公開ステータス','優先度','物件名_日本語','物件名_英語','郵便番号','住所_日本語','住所_英語','物件種別','募集区分','取引態様','賃料_円','管理費_円','敷金_月','礼金_月','契約形態','契約期間_月','面積_㎡','間取り','築年月','入居可能日','空室状況','駐車場','ペット','説明_日本語','説明_英語','画像フォルダURL','間取図URL','リコー3Dツアー　リンク','入力担当','最終確認日','日英整合','業務確認','業務確認日','技術確認','技術確認日','公開承認','公開承認日','公開予定日','公開日','公開URL','備考']
APPROVAL_FIELDS = ['業務確認','業務確認日','技術確認','技術確認日','公開承認','公開承認日']

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('物件情報アップロード管理ツール - Prototype'); self.geometry('1280x820'); self.minsize(1050,700)
        self.source_path=None; self.rows=[]; self.headers={}; self.current=None; self.pending={}; self.vars={}; self._build()

    def _build(self):
        top=ttk.Frame(self,padding=10); top.pack(fill='x')
        ttk.Button(top,text='Excelを開く',command=self.open_file).pack(side='left'); ttk.Button(top,text='検証',command=self.refresh_validation).pack(side='left',padx=6); ttk.Button(top,text='別名で保存',command=self.save_as).pack(side='left')
        self.file_label=ttk.Label(top,text='ファイル未選択'); self.file_label.pack(side='left',padx=14); self.summary=ttk.Label(top,text=''); self.summary.pack(side='right')
        pane=ttk.Panedwindow(self,orient='horizontal'); pane.pack(fill='both',expand=True,padx=10,pady=(0,10)); left=ttk.Frame(pane,padding=6); right=ttk.Frame(pane,padding=6); pane.add(left,weight=1); pane.add(right,weight=3)
        ttk.Label(left,text='物件一覧',font=('TkDefaultFont',11,'bold')).pack(anchor='w')
        self.tree=ttk.Treeview(left,columns=('id','name','status','errors'),show='headings',height=25)
        for c,w,label in [('id',75,'ID'),('name',210,'物件名'),('status',110,'公開状態'),('errors',60,'指摘')]: self.tree.heading(c,text=label); self.tree.column(c,width=w,anchor='w')
        self.tree.pack(fill='both',expand=True,pady=(5,0)); self.tree.bind('<<TreeviewSelect>>',self.on_select)
        notebook=ttk.Notebook(right); notebook.pack(fill='both',expand=True); self.detail=ttk.Frame(notebook,padding=8); self.validation=ttk.Frame(notebook,padding=8); self.approval=ttk.Frame(notebook,padding=8); notebook.add(self.detail,text='入力・編集'); notebook.add(self.validation,text='自動チェック'); notebook.add(self.approval,text='承認')
        self.canvas=tk.Canvas(self.detail,highlightthickness=0); scroll=ttk.Scrollbar(self.detail,orient='vertical',command=self.canvas.yview); self.form=ttk.Frame(self.canvas); self.form.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all'))); self.canvas.create_window((0,0),window=self.form,anchor='nw'); self.canvas.configure(yscrollcommand=scroll.set); self.canvas.pack(side='left',fill='both',expand=True); scroll.pack(side='right',fill='y')
        self.issue_tree=ttk.Treeview(self.validation,columns=('sev','field','msg'),show='headings');
        for c,w,label in [('sev',80,'重要度'),('field',180,'項目'),('msg',650,'内容')]: self.issue_tree.heading(c,text=label); self.issue_tree.column(c,width=w,anchor='w')
        self.issue_tree.pack(fill='both',expand=True); self.publish_label=ttk.Label(self.validation,text='',font=('TkDefaultFont',11,'bold')); self.publish_label.pack(anchor='w',pady=8)
        self.approval_vars={}
        for i,f in enumerate(APPROVAL_FIELDS):
            ttk.Label(self.approval,text=f).grid(row=i,column=0,sticky='w',pady=6,padx=(0,8)); v=tk.StringVar(); self.approval_vars[f]=v
            if f in {'業務確認','技術確認','公開承認'}: ttk.Combobox(self.approval,textvariable=v,values=['未確認','承認','差戻し'],state='readonly',width=20).grid(row=i,column=1,sticky='w')
            else: ttk.Entry(self.approval,textvariable=v,width=22).grid(row=i,column=1,sticky='w')
        ttk.Button(self.approval,text='承認欄を反映',command=self.apply_approval).grid(row=len(APPROVAL_FIELDS),column=0,columnspan=2,sticky='w',pady=12); ttk.Label(self.approval,text='※ 公開操作は行いません。3段階承認とNo-Go判定を確認する画面です。').grid(row=len(APPROVAL_FIELDS)+1,column=0,columnspan=2,sticky='w')

    def open_file(self):
        p=filedialog.askopenfilename(filetypes=[('Excel workbook','*.xlsx')]);
        if not p:return
        try:self.rows,self.headers=load_master(p)
        except Exception as e:messagebox.showerror('読込エラー',str(e));return
        self.source_path=p; self.file_label.config(text=Path(p).name); self.pending={}; self.populate_tree()
    def merged_row(self,row):
        data=dict(row); data.update(self.pending.get(row['excel_row'],{})); return data
    def duplicate_ids(self):
        ids=[self.merged_row(r).get('物件ID') for r in self.rows]; c=Counter(ids); return {k for k,v in c.items() if k not in (None,'') and v>1}
    def populate_tree(self):
        for x in self.tree.get_children():self.tree.delete(x)
        dupes=self.duplicate_ids(); total_errors=0
        for r in self.rows:
            d=self.merged_row(r); issues=validate_property(d,dupes); total_errors+=sum(i.severity=='ERROR' for i in issues); self.tree.insert('', 'end', iid=str(r['excel_row']), values=(d.get('物件ID'),d.get('物件名_日本語'),d.get('公開ステータス') or '',len(issues)))
        self.summary.config(text=f'{len(self.rows)}物件 / ERROR {total_errors}件')
    def on_select(self,_=None):
        sel=self.tree.selection();
        if not sel:return
        self.current=next(r for r in self.rows if r['excel_row']==int(sel[0])); self.build_form(); self.refresh_validation(); self.load_approval()
    def build_form(self):
        for w in self.form.winfo_children():w.destroy()
        self.vars={}; d=self.merged_row(self.current)
        for i,f in enumerate(EDITABLE_FIELDS):
            ttk.Label(self.form,text=f,width=24).grid(row=i,column=0,sticky='nw',pady=3); v=tk.StringVar(value=self.display(d.get(f))); self.vars[f]=v; ttk.Entry(self.form,textvariable=v,width=75).grid(row=i,column=1,sticky='ew',pady=3)
        self.form.columnconfigure(1,weight=1); ttk.Button(self.form,text='変更を一時反映',command=self.apply_form).grid(row=len(EDITABLE_FIELDS),column=1,sticky='e',pady=10)
    def display(self,v): return v.strftime('%Y-%m-%d') if isinstance(v,datetime) else ('' if v is None else str(v))
    def parse(self,f,s):
        s=s.strip();
        if not s:return None
        if f in {'賃料_円','管理費_円','契約期間_月'}:
            try:return int(s.replace(',',''))
            except:return s
        if f in {'敷金_月','礼金_月','面積_㎡'}:
            try:return float(s.replace(',',''))
            except:return s
        if f.endswith('日') or f=='築年月':
            try:return datetime.strptime(s,'%Y-%m-%d')
            except:return s
        return s
    def apply_form(self):
        if not self.current:return
        rownum=self.current['excel_row']; self.pending.setdefault(rownum,{})
        for f,v in self.vars.items():self.pending[rownum][f]=self.parse(f,v.get())
        self.populate_tree(); self.refresh_validation(); messagebox.showinfo('反映','変更を一時反映しました。元Excelはまだ変更していません。')
    def load_approval(self):
        d=self.merged_row(self.current)
        for f,v in self.approval_vars.items():v.set(self.display(d.get(f)))
    def apply_approval(self):
        if not self.current:return
        rownum=self.current['excel_row']; self.pending.setdefault(rownum,{})
        for f,v in self.approval_vars.items():self.pending[rownum][f]=self.parse(f,v.get())
        self.populate_tree(); self.refresh_validation()
    def refresh_validation(self):
        if not self.current:return
        for x in self.issue_tree.get_children():self.issue_tree.delete(x)
        d=self.merged_row(self.current); issues=validate_property(d,self.duplicate_ids())
        for i in issues:self.issue_tree.insert('', 'end', values=(i.severity,i.field,i.message))
        self.publish_label.config(text='公開判定: GO候補' if can_publish(d,issues) else '公開判定: NO-GO / 要確認')
    def save_as(self):
        if not self.source_path:return
        dest=filedialog.asksaveasfilename(defaultextension='.xlsx',filetypes=[('Excel workbook','*.xlsx')],initialfile=Path(self.source_path).stem+'_reviewed.xlsx');
        if not dest:return
        updates=[]
        for rownum,changes in self.pending.items():
            for f,val in changes.items():
                col=self.headers.get(f)
                if col:updates.append((rownum,col,val))
        try:save_updates_preserving_validations(self.source_path,dest,updates)
        except Exception as e:messagebox.showerror('保存エラー',str(e));return
        messagebox.showinfo('保存完了',f'元ファイルを変更せず、別名で保存しました。\n{dest}')

if __name__=='__main__':App().mainloop()
