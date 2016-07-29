from django.core.urlresolvers import reverse
from time import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.select import Select

from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from workshops.models import Person, Event, Tag, Role, Task


class SeleniumTestBase(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        start = time()
        cls.selenium = webdriver.PhantomJS()
        # cls.selenium = webdriver.Firefox()
        cls.selenium.set_window_size(1280, 500)
        print("run webbrowser {}".format(time() - start))
        print("browser version {}".format(cls.selenium.capabilities['version']))

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def tearDown(self):
        self.selenium.save_screenshot('selenium.png')
        super().tearDown()

    def go(self, view_name):
        url = reverse(view_name)
        full_url = '{}{}'.format(self.live_server_url, url)
        self.selenium.get(full_url)

    def fill(self, name, value):
        try:
            field = self.selenium.find_element_by_name(name)
        except NoSuchElementException as e:
            self.selenium.save_screenshot('selenium.png')
            raise AssertionError('No field with such name.') from e
        field.send_keys(value)

    def click_button(self, text):
        escaped_text = text.replace('"', '\\"')
        xpath_pattern = '//input[@value="{0}"]'
        xpath = xpath_pattern.format(escaped_text)
        elems = self.selenium.find_elements_by_xpath(xpath)
        if len(elems) == 0:
            raise AssertionError('No such button')
        elif len(elems) > 1:
            raise AssertionError('More than one button with such text')
        else:
            elems[0].click()

    def click_text(self, text):
        escaped_text = text.replace('"', '\\"')
        xpath_pattern = '//*[normalize-space(text())="{0}"]'
        xpath = xpath_pattern.format(escaped_text)
        elems = self.selenium.find_elements_by_xpath(xpath)
        if len(elems) == 0:
            raise AssertionError('No such text')
        elif len(elems) > 1:
            raise AssertionError('More than one text with such text')
        else:
            elems[0].click()

    def click_checkbox(self, name, value):
        # This does not work yet
        xpath_pattern = '//input[type=checkbox][name="{0}"][value="{1}"]'
        escaped_name = name.replace('"', '\\"')
        escaped_value = str(value).replace('"', '\\"')
        xpath = xpath_pattern.format(escaped_name, escaped_value)
        checkbox = self.selenium.find_element_by_xpath(xpath)
        checkbox.click()

    def get_selected_option(self, css_selector):
        select = self.selenium.find_element_by_css_selector(css_selector)
        return Select(select).first_selected_option.text


class SeleniumTests(SeleniumTestBase):
    def test_login(self):
        Person.objects.create_superuser(username='admin', personal='admin',
                                        family='admin', email='admin@admin.pl',
                                        password='admin')

        self.go('login')
        self.fill('username', 'admin')
        self.fill('password', 'admin')
        self.click_button('Log in')

        body = self.selenium.find_element_by_tag_name('body')
        self.assertIn(u'Uninvoice', body.text)

    def test_tasks(self):
        p = Person.objects.create_superuser(username='admin', personal='admin',
                                            family='admin',
                                            email='admin@admin.pl',
                                            password='admin')
        e = Event.objects.create(slug='ttt', host_id=2)
        ttt, _ = Tag.objects.get_or_create(name='TTT')
        e.tags.add(ttt)
        e.save()
        learner, _ = Role.objects.get_or_create(name='learner')
        Task.objects.create(role=learner, person=p, event=e)

        self.go('login')
        self.fill('username', 'admin')
        self.fill('password', 'admin')
        self.click_button('Log in')

        self.go('admin-dashboard')
        self.click_text('More')
        self.click_text('Tasks')

        self.assertEqual(self.get_selected_option('#id_event'), '---------')
