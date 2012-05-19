from django.utils.unittest.case import TestCase
from corehq.apps.users.models import WebUser
from corehq.apps.domain.shortcuts import create_domain
from django.test.client import Client
from django.core.urlresolvers import reverse
import os
from StringIO import StringIO
from dimagi.utils.post import tmpfile
from couchforms.models import SubmissionErrorLog, XFormInstance

def _clear_all_forms():
    for item in XFormInstance.view("couchforms/by_xmlns", include_docs=True, reduce=False).all():
        item.delete()

class SubmissionErrorTest(TestCase):
    
    def setUp(self):
        self.domain = create_domain("submit-errors")
        self.couch_user = WebUser.create(None, "test", "foobar")
        self.couch_user.add_domain_membership(self.domain.name, is_admin=True)
        self.couch_user.save()
        self.client = Client()
        self.client.login(**{'username': 'test', 'password': 'foobar'})
        self.url = reverse("receiver_post", args=[self.domain])
        _clear_all_forms()
        
    def tearDown(self):
        self.couch_user.delete()
        self.domain.delete()
        _clear_all_forms()
    def _submit(self, formname):
        file_path = os.path.join(os.path.dirname(__file__), "data", formname)
        with open(file_path, "rb") as f:
            return self.client.post(self.url, {
                "xml_submission_file": f
            })
        
    def testSubmitBadAttachmentType(self):
        res = self.client.post(self.url, {
                "xml_submission_file": "this isn't a file"
        })
        self.assertEqual(400, res.status_code)
        self.assertTrue("xml_submission_file" in res.content)
            
    def testSubmitDuplicate(self):
        file = os.path.join(os.path.dirname(__file__), "data", "simple_form.xml")
        with open(file) as f:
            res = self.client.post(self.url, {
                    "xml_submission_file": f
            })
            self.assertEqual(201, res.status_code)
            self.assertTrue("Thanks for submitting" in res.content)
        
        with open(file) as f:
            res = self.client.post(self.url, {
                    "xml_submission_file": f
            })
            self.assertEqual(201, res.status_code)
            self.assertTrue("Form is a duplicate" in res.content)
        
            
    def testSubmitBadXML(self):
        f, path = tmpfile()
        with f:
            f.write("this isn't even close to xml")
        with open(path) as f:
            res = self.client.post(self.url, {
                    "xml_submission_file": f
            })
            self.assertEqual(500, res.status_code)
            self.assertTrue("render_error" in res.content)
        
        # make sure we logged it
        log = SubmissionErrorLog.view("receiverwrapper/all_submissions_by_domain",
                                      reduce=False,
                                      include_docs=True,
                                      startkey=[self.domain.name, "by_type", "SubmissionErrorLog"],
                                      endkey=[self.domain.name, "by_type", "SubmissionErrorLog", {}]).one()
        
        self.assertTrue(log is not None)
        self.assertTrue("render_error" in log.problem)
        self.assertEqual("this isn't even close to xml", log.get_xml())
        
