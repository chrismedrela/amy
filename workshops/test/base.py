import traceback
import os
import re
import datetime
import xml.etree.ElementTree as ET
from django.test import TestCase
from ..models import \
    Airport, \
    Award, \
    Badge, \
    Person, \
    Site


TEMPLATE_STRING_IF_INVALID = 'XXX-unset-variable-XXX' # FIXME: get by importing settings


class TestBase(TestCase):
    '''Base class for Amy test cases.'''

    def setUp(self):
        '''Create standard objects.'''

        self._setUpSites()
        self._setUpAirports()
        self._setUpBadges()
        self._setUpPersons()

    def _setUpSites(self):
        '''Set up site objects.'''

        self.site_alpha = Site.objects.create(domain='alpha.edu',
                                              fullname='Alpha Site',
                                              country='Azerbaijan',
                                              notes='')

        self.site_beta = Site.objects.create(domain='beta.com',
                                             fullname='Beta Site',
                                             country='Brazil',
                                             notes='Notes\nabout\nBrazil\n')

    def _setUpAirports(self):
        '''Set up airport objects.'''

        self.airport_0_0 = Airport.objects.create(iata='AAA', fullname='Airport 0x0', country='Albania',
                                                  latitude=0.0, longitude=0.0)
        self.airport_0_50 = Airport.objects.create(iata='BBB', fullname='Airport 0x50', country='Bulgaria',
                                                   latitude=0.0, longitude=50.0)
        self.airport_50_100 = Airport.objects.create(iata='CCC', fullname='Airport 100x50', country='Cameroon',
                                                     latitude=50.0, longitude=100.0)

    def _setUpBadges(self):
        '''Set up badge objects.'''

        self.instructor = Badge.objects.create(name='instructor',
                                               title='Software Carpentry Instructor',
                                               criteria='Worked hard for this')

    def _setUpPersons(self):
        '''Set up person objects.'''

        self.hermione = Person.objects.create(personal='Hermione', middle=None, family='Granger',
                                              email='hermione@granger.co.uk', gender='F', active=True,
                                              airport=self.airport_0_0, github='herself',
                                              twitter='herself', url='http://hermione.org', slug='granger.h')

        self.harry = Person.objects.create(personal='Harry', middle=None, family='Potter',
                                           email='harry@hogwarts.edu', gender='M', active=True,
                                           airport=self.airport_0_50, github='hpotter',
                                           twitter=None, url=None, slug='potter.h')

        self.ron = Person.objects.create(personal='Ron', middle=None, family='Weasley',
                                         email='rweasley@ministry.gov.uk', gender='M', active=False,
                                         airport=self.airport_50_100, github=None,
                                         twitter=None, url='http://geocities.com/ron_weas', slug='weasley.ron')

        self.hermione_instructor = Award.objects.create(person=self.hermione,
                                                        badge=self.instructor,
                                                        awarded=datetime.date(2014, 01, 01))

    def _parse(self, content, save_to=None):
        """
        Parse the HTML page returned by the server.
        Must remove the DOCTYPE to avoid confusing Python's XML parser.
        Must also remove the namespacing, or use long-form names for elements.
        If save_to is a path, save a copy of the content to that file
        for debugging.
        """
        # Save the raw HTML if explicitly asked to (during debugging).
        if save_to:
            with open(save_to, 'w') as writer:
                w.write(content)

        # Report unfilled tags.
        if TEMPLATE_STRING_IF_INVALID in content:
            lines = content.split('\n')
            hits = [x for x in enumerate(lines)
                    if TEMPLATE_STRING_IF_INVALID in x[1]]
            msg = '"{0}" found in HTML page:\n'.format(TEMPLATE_STRING_IF_INVALID)
            assert not hits, msg + '\n'.join(['{0}: "{1}"'.format(h[0], h[1].rstrip())
                                              for h in hits])

        # Make the content safe to parse.
        content = re.sub('<!DOCTYPE [^>]*>', '', content)
        content = re.sub('<html[^>]*>', '<html>', content)
        content = content.replace('&nbsp;', ' ')

        # Parse if we can.
        try:
            doc = ET.XML(content)
            return doc
        # ...and save in a uniquely-named file if we can't.
        except ET.ParseError, e:
            stack = traceback.extract_stack()
            callers = [s[2] for s in stack] # get function/method names
            while callers and not callers[-1].startswith('test'):
                callers.pop()
            assert callers, 'Internal error: unable to find caller'
            caller = callers[-1]
            err_dir = 'htmlerror'
            if not os.path.isdir(err_dir):
                os.mkdir(err_dir)
            filename = os.path.join(err_dir, '{0}.html'.format(caller))
            with open(filename, 'w') as writer:
                writer.write(content)
            assert False, 'HTML parsing failed: {0}'.format(str(e))

    def _check_status_code_and_parse(self, response, expected):
        '''Check the status code, then parse if it is OK.'''
        assert response.status_code == expected, \
            'Got status code {0}, expected {1}'.format(response.status_code, expected)
        return self._parse(response.content)

    def _check_0(self, doc, xpath, msg):
        '''Check that there are no nodes of a particular type.'''
        nodes = doc.findall(xpath)
        assert len(nodes) == 0, (msg + ': got {0}'.format(len(nodes)))

    def _get_1(self, doc, xpath, msg):
        '''Get exactly one node from the document, checking that there _is_ exactly one.'''
        nodes = doc.findall(xpath)
        assert len(nodes) == 1, (msg + ': got {0}'.format(len(nodes)))
        return nodes[0]

    def _get_N(self, doc, xpath, msg, expected=None):
        '''Get all matching nodes from the document, checking the count if provided.'''
        nodes = doc.findall(xpath)
        if expected is not None:
            assert len(nodes) == expected, (msg + ': expected {0}, got {1}'.format(expected, len(nodes)))
        return nodes
