#!/usr/bin/env python3
"""Regression tests. Run with the same Python as setup; --browser runs real browser checks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

SCRIPTS = Path(__file__).resolve().parent
PARSER = argparse.ArgumentParser()
PARSER.add_argument('--browser', action='store_true')
ARGS = PARSER.parse_args()
BASE = Path.cwd() / 'work/ref2game-tests'
BASE.mkdir(parents=True, exist_ok=True)
RUN = Path(tempfile.mkdtemp(prefix='run-', dir=BASE)).resolve()


def command(args, cwd=RUN, code=0, timeout=70):
    r = subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True, text=True, encoding='utf-8', timeout=timeout)
    if r.returncode != code:
        raise AssertionError(f'{args}\nexit={r.returncode}, expected={code}\n{r.stdout}\n{r.stderr}')
    return r


class Workflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = RUN / 'game with spaces'
        command([sys.executable, SCRIPTS/'setup.py', cls.project, '--genre', 'blank'])
        from PIL import Image
        Image.new('RGBA', (16, 8), (255, 0, 0, 255)).save(cls.project/'art/gen/hero_sheet.png')
        (cls.project/'art/prompts/hero.txt').write_text('preserve this prompt', encoding='utf-8')

    def test_setup_preserves_edits(self):
        f = self.project/'live/audio.js'
        f.write_text('// user audio edit\n', encoding='utf-8')
        command([sys.executable, SCRIPTS/'setup.py', self.project, '--genre', 'side'])
        self.assertEqual(f.read_text(encoding='utf-8'), '// user audio edit\n')
        self.assertIn('ITEMS', (self.project/'live/sim.js').read_text(encoding='utf-8'))

    def test_assets_only(self):
        p = RUN/'asset only'
        command([sys.executable, SCRIPTS/'setup.py', p, '--mode', 'assets'])
        self.assertFalse((p/'live').exists())
        from PIL import Image
        Image.new('RGBA', (8, 8), (255, 0, 0, 255)).save(p/'art/gen/icon.png')
        command([sys.executable, SCRIPTS/'prep.py'], cwd=p)
        command([sys.executable, SCRIPTS/'pack.py', '--name', 'icons', '--zip'], cwd=p)
        self.assertFalse((p/'dist/icons/game').exists())
        self.assertTrue((p/'dist/icons/assets/textures/icon.png').exists())

    def test_archive_preserves_sources_and_checksums(self):
        command([sys.executable, SCRIPTS/'pack.py', '--name', 'complete', '--zip'], cwd=self.project)
        with zipfile.ZipFile(self.project/'dist/complete.zip') as z:
            self.assertIn('complete/assets/source/hero_sheet.png', z.namelist())
            self.assertIn('complete/project/art/prompts/hero.txt', z.namelist())
            self.assertIn('complete/project/ref2game.json', z.namelist())
            hashes = json.loads(z.read('complete/checksums.json'))
            for f, h in hashes.items():
                self.assertEqual(hashlib.sha256(z.read('complete/'+f)).hexdigest(), h)

    def test_invalid_names_preserve_sentinel(self):
        sentinel = RUN/'sentinel.txt'
        sentinel.write_text('keep', encoding='utf-8')
        for name in ['..', '../outside', str(RUN/'outside'), 'a/b', 'a\\b', 'CON']:
            with self.subTest(name=name):
                command([sys.executable, SCRIPTS/'pack.py', '--name', name], cwd=self.project, code=2)
                self.assertEqual(sentinel.read_text(), 'keep')

    def test_existing_unmarked_directory_preserved(self):
        target = self.project/'dist/unowned'
        target.mkdir(parents=True, exist_ok=True)
        (target/'keep.txt').write_text('keep')
        command([sys.executable, SCRIPTS/'pack.py', '--name', 'unowned', '--replace'], cwd=self.project, code=2)
        self.assertTrue((target/'keep.txt').exists())

    def test_output_cannot_be_source_directory(self):
        before=(self.project/'live/sim.js').read_bytes()
        for out in ['.', 'art/build', 'live/build']:
            command([sys.executable,SCRIPTS/'pack.py','--name','safe','--out',out],cwd=self.project,code=2)
        self.assertEqual(before,(self.project/'live/sim.js').read_bytes())

    def test_replace_and_failed_build_preserve_previous(self):
        command([sys.executable, SCRIPTS/'pack.py', '--name', 'replace', '--zip'], cwd=self.project)
        command([sys.executable, SCRIPTS/'pack.py', '--name', 'replace', '--zip', '--replace'], cwd=self.project)
        f=self.project/'live/assets.js'; original=f.read_bytes()
        before=(self.project/'dist/replace.zip').read_bytes()
        try:
            f.write_text('window.ASSETS = {"missing":{}};',encoding='utf-8')
            command([sys.executable, SCRIPTS/'pack.py', '--name', 'replace', '--zip', '--replace'], cwd=self.project, code=2)
            self.assertEqual(before,(self.project/'dist/replace.zip').read_bytes())
        finally:
            f.write_bytes(original)

    @unittest.skipUnless(ARGS.browser, 'enable --browser')
    def test_browser_qa_rejects_empty_and_missing_coverage(self):
        p=RUN/'empty'; (p/'live').mkdir(parents=True)
        (p/'live/index.html').write_text('<link rel="icon" href="data:,"><canvas id="c"></canvas><script>window.LIB={};window.SCENE={QA:()=>({states:[],cycles:{}})};window.__ready=true;</script>')
        command(['node',SCRIPTS/'qa.mjs'],cwd=p,code=2)
        self.assertIn('at least one', (p/'frames/qa/report.json').read_text())
        command(['node',SCRIPTS/'qa.mjs','--require','match'],cwd=self.project,code=2)
        self.assertIn('required QA coverage', (self.project/'frames/qa/report.json').read_text())

    @unittest.skipUnless(ARGS.browser, 'enable --browser')
    def test_browser_all_templates(self):
        for genre in ['side','top','blank']:
            with self.subTest(genre=genre):
                p=RUN/('template '+genre)
                command([sys.executable,SCRIPTS/'setup.py',p,'--genre',genre])
                command(['node',SCRIPTS/'qa.mjs'],cwd=p)
                command(['node',SCRIPTS/'render.mjs','stills','0,0.5'],cwd=p)
                command(['node',SCRIPTS/'livecheck.mjs','--keys','ArrowRight:press@0','--shots','0','--assert','!!SCENE.state && SCENE.state.steps > 0'],cwd=p)

    @unittest.skipUnless(ARGS.browser, 'enable --browser')
    def test_browser_behavior_reload_and_extracted_build(self):
        scenario=RUN/'collect.json'
        scenario.write_text(json.dumps({'steps':[
            {'click':[560,420]}, {'expect':'SCENE.state.got[0] >= 0','label':'click collects the item'},
            {'key':'KeyP'}, {'expect':'window.__REF2GAME_TEST__.snapshot().paused'},
            {'expect':'(window.savedSteps = SCENE.state.steps, true)'}, {'wait':120},
            {'expect':'SCENE.state.steps === window.savedSteps','label':'pause stops simulation'},
            {'key':'KeyR'}, {'expect':'SCENE.state.got.every(x => x === -1)','label':'restart clears collected items'},
            {'key':'KeyP'}, {'click':[560,420]}, {'expect':'SCENE.state.got[0] >= 0'}
        ]}),encoding='utf-8')
        command(['node',SCRIPTS/'livecheck.mjs','--scenario',scenario,'--reload','--reload-fields','got'],cwd=self.project)
        command([sys.executable,SCRIPTS/'pack.py','--name','playable','--zip'],cwd=self.project)
        extracted=RUN/'extracted'; extracted.mkdir()
        with zipfile.ZipFile(self.project/'dist/playable.zip') as z: z.extractall(extracted)
        # Serve the actual unpacked folder through the same shared server helper.
        js=RUN/'check-extracted.mjs'
        js.write_text("import {serve} from "+json.dumps((SCRIPTS/'runtime.mjs').as_uri())+";\nimport {spawnSync} from 'node:child_process';\nconst s=await serve(process.argv[2]);\nconst {spawn}=await import('node:child_process');\ntry { const result=await new Promise(resolve=>{const p=spawn(process.execPath,[process.argv[3],'--url',s.url+'/index.html','--scenario',process.argv[4]],{stdio:'inherit'});p.on('exit',resolve);});process.exitCode=result; } finally {await s.close();}\n",encoding='utf-8')
        command(['node',js,extracted/'playable/game',SCRIPTS/'livecheck.mjs',scenario],cwd=RUN)

    @unittest.skipUnless(ARGS.browser, 'enable --browser')
    def test_false_assertion_fails(self):
        command(['node',SCRIPTS/'livecheck.mjs','--keys','ArrowRight:press@0','--shots','0','--assert','false','--timeout','100'],cwd=self.project,code=2)

    @unittest.skipUnless(ARGS.browser, 'enable --browser')
    def test_no_assertions_is_not_gameplay_pass(self):
        common=['node',SCRIPTS/'livecheck.mjs','--keys','ArrowRight:press@0','--shots','0']
        command(common,cwd=self.project,code=2)
        command([*common,'--smoke'],cwd=self.project)
        report=json.loads((self.project/'frames/livecheck/report.json').read_text())
        self.assertEqual(report['functional'],'not_tested')

    @unittest.skipUnless(ARGS.browser, 'enable --browser')
    def test_qa_uses_game_dimensions(self):
        p=RUN/'small view'; (p/'live').mkdir(parents=True)
        (p/'live/index.html').write_text('''<link rel="icon" href="data:,"><canvas id="c" width="320" height="180"></canvas><script>
window.SCENE={QA:()=>({states:[['start',{t:0}]],cycles:{}}),render:()=>{window.__UI=[{k:'text',id:'outside',s:'bad',x:400,y:20,w:40,h:20}];}};window.__ready=true;
</script>''')
        (p/'ref2game.json').write_text(json.dumps({'qa':{'required':['states'],'not_applicable':['rig']}}))
        command(['node',SCRIPTS/'qa.mjs'],cwd=p,code=2)
        report=json.loads((p/'frames/qa/report.json').read_text())
        self.assertTrue(any('leaves the screen' in f for f in report['fails']))
        self.assertEqual(report['coverage']['rig']['status'],'not_applicable')


if __name__ == '__main__':
    print(f'Test artifacts: {RUN}',flush=True)
    unittest.main(argv=[sys.argv[0]],verbosity=2)
