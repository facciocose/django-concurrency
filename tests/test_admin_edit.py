from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from concurrency.forms import VersionFieldSigner
from tests.base import AdminTestCase, SENTINEL
from tests.models import SimpleConcurrentModel

# @pytest.mark.django_db
# @pytest.mark.admin
# def test_creation(superuser, app):
#     url = reverse('admin:concurrency_simpleconcurrentmodel_add')
#     res = app.get(url, user=superuser.username)
#
#     form = res.form
#     form['username'] = 'CHAR'
#     res = form.submit().follow()
#     assert SimpleConcurrentModel.objects.filter(username='CHAR').exists()
#     assert SimpleConcurrentModel.objects.get(username='CHAR').version > 0
#
#     # self.assertTrue(SimpleConcurrentModel.objects.filter(username='CHAR').exists())
#     # self.assertGreater(SimpleConcurrentModel.objects.get(username='CHAR').version, 0)
#
#
# @pytest.mark.django_db
# @pytest.mark.functional
# def test_standard_update(superuser, concurrentmodel, app):
#     url = reverse('admin:concurrency_simpleconcurrentmodel_change',
#                   args=[concurrentmodel.pk])
#     res = app.get(url, user=superuser.username)
#
#     target = res.context['original']
#
#     old_version = target.version
#     form = res.form
#     form['username'] = 'UPDATED'
#     res = form.submit().follow()
#     target = SimpleConcurrentModel.objects.get(pk=target.pk)
#     new_version = target.version
#
#     assert new_version > old_version

# @pytest.mark.django_db
# @pytest.mark.functional
# def test_conflict(superuser, concurrentmodel, app):
#     url = reverse('admin:concurrency_simpleconcurrentmodel_change',
#                   args=[concurrentmodel.pk])
#     res = app.get(url, user=superuser.username)
#     form = res.form
#     concurrentmodel.save()  # create conflict here
#
#     res = form.submit()
#
#     assert 'original' in res.context
#     assert res.context['adminform'].form.errors
#     assert _('Record Modified') in str(res.context['adminform'].form.errors)
from tests.util import nextname


class TestConcurrentModelAdmin(AdminTestCase):

    def test_standard_update(self):
        target, __ = SimpleConcurrentModel.objects.get_or_create(username='aaa')
        url = reverse('admin:concurrency_simpleconcurrentmodel_change', args=[target.pk])
        res = self.app.get(url, user='sax')
        target = res.context['original']
        old_version = target.version
        form = res.form
        form['username'] = 'UPDATED'
        res = form.submit().follow()
        target = SimpleConcurrentModel.objects.get(pk=target.pk)
        new_version = target.version
        self.assertGreater(new_version, old_version)

    def test_creation(self):
        url = reverse('admin:concurrency_simpleconcurrentmodel_add')
        res = self.app.get(url, user='sax')
        form = res.form
        form['username'] = 'CHAR'
        res = form.submit().follow()
        self.assertTrue(SimpleConcurrentModel.objects.filter(username='CHAR').exists())
        self.assertGreater(SimpleConcurrentModel.objects.get(username='CHAR').version, 0)

    def test_conflict(self):
        target, __ = SimpleConcurrentModel.objects.get_or_create(username='aaa')
        url = reverse('admin:concurrency_simpleconcurrentmodel_change', args=[target.pk])
        res = self.app.get(url, user='sax')

        form = res.form
        target.save()  # create conflict here

        res = form.submit()

        self.assertIn('original', res.context)
        self.assertTrue(res.context['adminform'].form.errors,
                        res.context['adminform'].form.errors)
        self.assertIn(_('Record Modified'),
                      str(res.context['adminform'].form.errors),
                      res.context['adminform'].form.errors)


class TestAdminEdit(AdminTestCase):

    def _create_conflict(self, pk):
        u = SimpleConcurrentModel.objects.get(pk=pk)
        u.username = SENTINEL
        u.save()

    def test_creation(self):
        url = reverse('admin:concurrency_simpleconcurrentmodel_add')
        res = self.app.get(url, user='sax')
        form = res.form
        form['username'] = 'CHAR'
        res = form.submit().follow()
        self.assertTrue(SimpleConcurrentModel.objects.filter(username='CHAR').exists())
        self.assertGreater(SimpleConcurrentModel.objects.get(username='CHAR').version, 0)

    def test_creation_with_customform(self):
        url = reverse('admin:concurrency_simpleconcurrentmodel_add')
        res = self.app.get(url, user='sax')
        form = res.form
        username = next(nextname)
        form['username'] = username
        res = form.submit().follow()
        self.assertTrue(SimpleConcurrentModel.objects.filter(username=username).exists())
        self.assertGreater(SimpleConcurrentModel.objects.get(username=username).version, 0)

        #test no other errors are raised
        res = form.submit()
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "SimpleConcurrentModel with this Username already exists.")

    def test_standard_update(self):
        target, __ = SimpleConcurrentModel.objects.get_or_create(username='aaa')
        url = reverse('admin:concurrency_simpleconcurrentmodel_change', args=[target.pk])
        res = self.app.get(url, user='sax')
        target = res.context['original']
        old_version = target.version
        form = res.form
        form['username'] = 'UPDATED'
        res = form.submit().follow()
        target = SimpleConcurrentModel.objects.get(pk=target.pk)
        new_version = target.version
        self.assertGreater(new_version, old_version)

    def test_conflict(self):
        target, __ = SimpleConcurrentModel.objects.get_or_create(username='aaa')
        assert target.version
        url = reverse('admin:concurrency_simpleconcurrentmodel_change', args=[target.pk])
        res = self.app.get(url, user='sax')
        form = res.form

        target.save()  # create conflict here
        res = form.submit()
        self.assertIn('original', res.context)
        self.assertTrue(res.context['adminform'].form.errors,
                        res.context['adminform'].form.errors)
        self.assertIn(_('Record Modified'),
                      str(res.context['adminform'].form.errors),
                      res.context['adminform'].form.errors)

    def test_sanity_signer(self):
        target, __ = SimpleConcurrentModel.objects.get_or_create(username='aaa')
        url = reverse('admin:concurrency_simpleconcurrentmodel_change', args=[target.pk])
        res = self.app.get(url, user='sax')
        form = res.form
        version1 = int(str(form['version'].value).split(":")[0])
        form['version'] = VersionFieldSigner().sign(version1)
        form['date_field'] = 'esss2010-09-01'
        response = form.submit()
        self.assertIn('original', response.context)
        self.assertTrue(response.context['adminform'].form.errors,
                        response.context['adminform'].form.errors)
        form = response.context['adminform'].form
        version2 = int(str(form['version'].value()).split(":")[0])
        self.assertEqual(version1, version2)
