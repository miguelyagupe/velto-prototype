import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from awl.engine import validate,ValidationError,captions,render,qa,run

class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name)
        for file in ('capture.mp4','voice.wav','evidence.json'): (self.base/file).write_text('fixture')
        (self.base/'captions.srt').write_text('1\n00:00:00,000 --> 00:00:01,900\nA test.\n')
        (self.base/'proofs.json').write_text(json.dumps({'proofs':[{'id':'p1','path':'evidence.json','claim':'Fixture for unit testing only'}]}))
        self.d={'version':1,'width':1920,'height':1080,'fps':30,'narration':'voice.wav','captions':'captions.srt','proofs':'proofs.json','scenes':[{'source':'capture.mp4','in':0,'out':2,'destination':0,'license':'original fixture','proof_id':'p1'}]}
    def tearDown(self): self.tmp.cleanup()
    def check(self):
        p=self.base/'timeline.json';p.write_text(json.dumps(self.d));return validate(p,inspect_media=False)
    def test_valid(self): self.assertEqual(self.check()['duration'],2)
    def test_missing_asset(self):
        self.d['scenes'][0]['source']='missing.mp4'
        with self.assertRaisesRegex(ValidationError,'does not exist'): self.check()
    def test_negative_in(self):
        self.d['scenes'][0]['in']=-1
        with self.assertRaisesRegex(ValidationError,'invalid source interval'): self.check()
    def test_reversed_cut(self):
        self.d['scenes'][0]['out']=0
        with self.assertRaisesRegex(ValidationError,'invalid source interval'): self.check()
    def test_gap(self):
        self.d['scenes'][0]['destination']=1
        with self.assertRaisesRegex(ValidationError,'gap/overlap'): self.check()
    def test_unproven_scene(self):
        self.d['scenes'][0]['proof_id']='invented'
        with self.assertRaisesRegex(ValidationError,'unknown proof'): self.check()
    def test_missing_proof_file(self):
        (self.base/'evidence.json').unlink()
        with self.assertRaisesRegex(ValidationError,'proof.path'): self.check()
    def test_missing_license(self):
        self.d['scenes'][0]['license']=''
        with self.assertRaisesRegex(ValidationError,'license'): self.check()
    def test_nan_time(self):
        self.d['scenes'][0]['in']=float('nan')
        with self.assertRaisesRegex(ValidationError,'finite'): self.check()
    def test_crop_expression_rejected(self):
        self.d['scenes'][0]['crop']={'x':'iw/2','y':0,'width':100,'height':100}
        with self.assertRaisesRegex(ValidationError,'invalid crop'): self.check()
    def test_subtitles_overrun(self):
        (self.base/'captions.srt').write_text('1\n00:00:00,000 --> 00:00:03,000\nBad.\n')
        with self.assertRaisesRegex(ValidationError,'beyond'): self.check()
    def test_subtitles_overlap(self):
        (self.base/'captions.srt').write_text('1\n00:00:00,000 --> 00:00:01,500\nOne\n\n2\n00:00:01,000 --> 00:00:01,800\nTwo\n')
        with self.assertRaisesRegex(ValidationError,'overlap'): self.check()
    def test_media_out_of_bounds(self):
        self.check()
        fake={'format':{'duration':'1'},'streams':[{'codec_type':'video','width':1920,'height':1080}]}
        with patch('awl.engine.probe',return_value=fake), self.assertRaisesRegex(ValidationError,'out exceeds'):
            validate(self.base/'timeline.json')

class IntegrationTests(unittest.TestCase):
    def test_render_decode_and_qa(self):
        # A generated fixture validates the renderer, never an episode or demo claim.
        with tempfile.TemporaryDirectory() as tmp:
            b=Path(tmp)
            run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=320x180:rate=30','-t','2','-c:v','libx264','-threads','1',b/'fixture.mp4'])
            run(['ffmpeg','-v','error','-y','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','2',b/'audio.wav'])
            (b/'proof.txt').write_text('Synthetic integration fixture; not production evidence.')
            (b/'proofs.json').write_text(json.dumps({'proofs':[{'id':'fixture','path':'proof.txt','claim':'Synthetic render fixture'}]}))
            (b/'captions.srt').write_text('1\n00:00:00,000 --> 00:00:01,900\nIntegration fixture\n')
            d={'version':1,'width':320,'height':180,'fps':30,'narration':'audio.wav','captions':'captions.srt','proofs':'proofs.json','scenes':[{'source':'fixture.mp4','in':0,'out':1,'destination':0,'license':'generated test fixture','proof_id':'fixture'},{'source':'fixture.mp4','in':1,'out':2,'destination':1,'license':'generated test fixture','proof_id':'fixture','crop':{'x':0,'y':0,'width':160,'height':90}}]}
            p=b/'timeline.json';p.write_text(json.dumps(d));out=b/'out.mp4'
            r=render(p,out);self.assertTrue(out.is_file());self.assertEqual(r['paid_api_calls'],0)
            report=qa(out,p)
            self.assertTrue(report['technical_pass'],report['errors'])
            self.assertFalse(report['editorial_approved']);self.assertFalse(report['publishable'])
            self.assertTrue(out.with_suffix('.srt').is_file())

if __name__=='__main__': unittest.main()
