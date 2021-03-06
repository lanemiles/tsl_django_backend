# relevant imports
from tsl_news.models import Section, Author, Article, WaitingArticle, User
from django.test import Client
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import setup_test_environment
from django.utils import timezone
from datetime import datetime
import json

setup_test_environment()


class ArticleTests(TestCase):

    # set up one article
    def setUp(self):
        # create section
        news = Section(name='News')
        news.save()
        # create author
        auth = Author(name='First Last')
        auth.save()
        # create article properties
        new_article = Article(headline='Some test article')
        new_article.pub_date = datetime.strptime('May 26, 2012', '%B %d, %Y')
        new_article.section = news

        # save so far
        new_article.save()

        new_article.authors.add(auth)
        new_article.article_body = "This is a test article.\n\nThat has a second paragraph."
        new_article.url = "http://tsl.pomona.edu/"
        new_article.is_featured = True;

        # save so far
        new_article.save()

        # and now have some user favorite it
        user = User(iphone_udid='devicetest')
        user.save()
        user.favorite_articles.add(new_article)
        user.save()

    # now, we want to make sure we get the json correctly
    def test_article_data_in_json(self):
        client = Client()
        req = client.get(reverse('indiv_article_view_plus_favorite', kwargs={'userID' : 'test', 'articleID' : 1}))
        # check to make sure headline is there
        self.assertContains(req, 'Some test article', status_code=200)
        # now check for author
        self.assertContains(req, 'First Last', status_code=200)
        # and then body
        self.assertContains(req, json.dumps('This is a test article.\n\nThat has a second paragraph.'), status_code=200)
        # and now date
        self.assertContains(req, 'May 26, 2012', status_code=200)

    # make sure only favorite if user has
    def test_no_erroneous_favorite(self):
        client = Client()
        req = client.get(reverse('indiv_article_view_plus_favorite', kwargs={'userID' : 'test', 'articleID' : 1}))
        # check for JSON of favorite
        self.assertContains(req, '"favorited": "false"', status_code=200)

    # make sure favorite does work when it should
    def test_favorites_appear_in_json(self):
        client = Client()
        req = client.get(reverse('indiv_article_view_plus_favorite', kwargs={'userID' : 'devicetest', 'articleID' : 1}))
        # check for JSON of favorite
        self.assertContains(req, '"favorited": "true"', status_code=200)

    # make sure the featured articles appear correctly
    def test_getting_featured_articles(self):
        client = Client()
        req = client.get(reverse('featured_list'))
        # check for JSON of favorite
        self.assertContains(req, 'Some test article', status_code=200)

    # make sure the sections appear correctly
    def test_getting_sections(self):
        client = Client()
        req = client.get(reverse('section_list', kwargs={'sectionName': 'News'}))
        # check for JSON of favorite
        self.assertContains(req, 'Some test article', status_code=200)

    # now test the REST functionality

    # test adding favorite from a previously unfavorited article
    def test_add_favorite(self):
        client = Client()
        # make sure first not favorited
        req = client.get(reverse('indiv_article_view_plus_favorite', kwargs={'userID': 'favoriteaddtest', 'articleID' : 1}))
        self.assertContains(req, '"favorited": "false"', status_code=200)

        # now favorite
        req = client.get(reverse('user_add_favorite', kwargs={'userID': 'favoriteaddtest', 'articleID' : 1}))
        
        # make sure they have now favorited
        req = client.get(reverse('indiv_article_view_plus_favorite', kwargs={'userID': 'favoriteaddtest', 'articleID' : 1}))
        self.assertContains(req, '"favorited": "true"', status_code=200)

    # test removing favorite from a previously favorited article
    def test_remove_favorite(self):
        client = Client()
        # make sure first favorited
        req = client.get(reverse('user_add_favorite', kwargs={'userID': 'favoriteaddtest', 'articleID' : 1}))
        req = client.get(reverse('indiv_article_view_plus_favorite', kwargs={'userID': 'favoriteaddtest', 'articleID' : 1}))
        self.assertContains(req, '"favorited": "true"', status_code=200)

        # now unfavorite
        req = client.get(reverse('user_remove_favorite', kwargs={'userID': 'favoriteaddtest', 'articleID' : 1}))
        
        # make sure they have not favorited
        req = client.get(reverse('indiv_article_view_plus_favorite', kwargs={'userID': 'favoriteaddtest', 'articleID' : 1}))
        self.assertContains(req, '"favorited": "false"', status_code=200)

    # test adding an article to the database from the form
    def test_adding_article_to_database(self):
        client = Client()

        # no WaitingArticles before
        wait_count = len(list(WaitingArticle.objects.all()))
        self.assertEqual(wait_count, 0)

        # add one
        resp = self.client.post(reverse('add_article_form'), {'url' : 'http://tsl.pomona.edu/articles/2015/4/24/news/6415-chaplaincy-budget-discussions-arise-during-committee-review'})
        self.assertEqual(resp.status_code, 301)

        # count is 0 again
        wait_count = len(list(WaitingArticle.objects.all()))
        self.assertEqual(wait_count, 0)

        # article is in database
        article, did_create = Article.objects.get_or_create(url='http://tsl.pomona.edu/articles/2015/4/24/news/6415-chaplaincy-budget-discussions-arise-during-committee-review')
        self.assertEqual(did_create, False)

    # test that adding article adds fields correctly
    def test_verifying_added_article_information(self):
        client = Client()

         # add one
        resp = self.client.post(reverse('add_article_form'), {'url' : 'http://tsl.pomona.edu/articles/2015/4/24/news/6415-chaplaincy-budget-discussions-arise-during-committee-review'})
        self.assertEqual(resp.status_code, 301)

        # make sure data in database is correct

        # get article from database
        article = Article.objects.get(url='http://tsl.pomona.edu/articles/2015/4/24/news/6415-chaplaincy-budget-discussions-arise-during-committee-review')

        # verify authors
        auth = article.authors.all()
        auth_list = []
        for author in auth:
            auth_list.append(author.name)
        self.assertEqual(auth_list, ["Kevin Tidmarsh"])
        # headline
        self.assertEqual(article.headline, 'Chaplaincy Budget Discussions Arise During Committee Review')
        # date
        self.assertEqual(article.pub_date.strftime("%B %d, %Y"), 'April 24, 2015')
        # section
        self.assertEqual(article.section.name, 'News')
        # and body is all paragraphs separated by '\n\n'
        if "\r" in article.article_body:
            self.assertEqual(True, False)
        if "\n\n\n" in article.article_body:
            self.assertEqual(True, False)
        if " \n " in article.article_body:
            self.assertEqual(True, False)

    # adding the same URL should not add a duplicate
    def test_adding_duplicate_url_should_not_make_duplicate(self):
        client = Client()

        # add then add again and we should have the same count
        resp = self.client.post(reverse('add_article_form'), {'url' : 'http://tsl.pomona.edu/articles/2015/4/24/news/6409-city-of-claremont-and-5c-students-join-forces-for-energy-prize'})
        self.assertEqual(resp.status_code, 301)

        # get article count before re adding
        article_count = len(list(Article.objects.all()))

        # add same one
        resp = self.client.post(reverse('add_article_form'), {'url' : 'http://tsl.pomona.edu/articles/2015/4/24/news/6409-city-of-claremont-and-5c-students-join-forces-for-energy-prize'})
        self.assertEqual(resp.status_code, 301)

        # count should be the same
        article_count_after = len(list(Article.objects.all()))
        self.assertEqual(article_count_after, article_count)

