
import codecs

from aqt.qt import *
from aqt.webview import AnkiWebView
from aqt.utils import showInfo, tooltip

from ..kanji import kanji_search, find_kanji_in_tier, KanjiSets
from ..web import html_doc, tier_html



class KanjiGrid(QDialog):


    def __init__(self, mw):
        super(KanjiGrid, self).__init__(mw)
        self.mw = mw
        self.sets = KanjiSets()

        self.title = "Kanji Grid"
        self.setModal(True)
        self.setLayout(self.ui())
        self.setWindowTitle(self.title)
        self.resize(1200,800)

        self.web.loadFinished.connect(super(KanjiGrid, self).show)
        self.web.loadFinished.connect(self.mw.progress.finish)
    

    def show(self, group_by):
        self.mw.progress.start(immediate=True, label="Generating Kanji Grid...")
        self.web.stdHtml(self.generate(group_by))


    def ui(self):
        self.web = AnkiWebView()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.web)
        layout.addLayout(self.ui_buttons())

        return layout

    
    def ui_buttons(self):
        layout = QHBoxLayout()

        sh = QPushButton("Save HTML")
        sh.clicked.connect(self.savehtml)
        layout.addWidget(sh)

        sp = QPushButton("Save PDF")
        sp.clicked.connect(self.savepdf)
        layout.addWidget(sp)

        bb = QPushButton("Close")
        bb.clicked.connect(self.reject)
        layout.addWidget(bb)

        return layout


    def generate(self, group_by, separator=' | '):
        config = self.mw.addonManager.getConfig(__name__)
        self.last_group_by = group_by
        
        exclusions = {}
        deck_ids = [x for x in config['decks'] if config['decks'][x] > 0]

        for note in config['notes']:

            if note not in exclusions:
                exclusions[note] = []

            model = self.mw.col.models.get(note)
            field_names = [f['name'] for f in model['flds']]

            for fn in config['notes'][note]:
                if not config['notes'][note][fn]:
                    exclusions[note].append(field_names.index(fn))


        kanji = kanji_search(deck_ids, exclusions)
        tiers = self.sets[group_by]
        tier_docs = []

        for tier in tiers:
            tier_name = list(tier.keys())[0]
            tier_char = list(tier.values())[0]
            
            found, missing = find_kanji_in_tier(kanji, tier_char)
            tier_docs.append(tier_html(
                tier_name, 
                kanji,
                found, 
                missing, 
                cols=int(config['cols']), 
                threshold=int(config['threshold']),
                separator=separator,
                force_percent=True,
            ))
            for k in found:
                del kanji[k]

        tier_docs.append(tier_html(
            "Additional Kanji" if group_by != 'None' else 'All Kanji',
            kanji,
            list(kanji.keys()),
            [],
            cols=int(config['cols']), 
            threshold=int(config['threshold']),
            separator=separator,
        ))

        return html_doc(', '.join(sorted([self.mw.col.decks.get(x)['name'] for x in deck_ids])), ''.join(tier_docs), threshold=config['threshold'])



    def savehtml(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save KanjiGrid - HTML", "", "Web Files (*.html)")

        if filename != "":
            self.mw.progress.start(immediate=True, label="Saving HTML Document")
            html = self.generate(self.last_group_by, separator='\n')

            with codecs.open(filename, 'w', 'utf-8') as fh:
                fh.write(html)

            self.mw.progress.finish()
            showInfo("HTML Document saved to: %s!" % filename)


    def savepdf(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save KanjiGrid - PDF", "", "Portable Document Files (*.pdf)")

        if filename != "":
            self.mw.progress.start(immediate=True, label="Saving PDF")
            self.web.page().printToPdf(filename)
            self.mw.progress.finish()
            showInfo("PDF saved to: %s!" % filename)
