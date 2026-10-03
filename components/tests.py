from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from components.models import Component, Category, ReuseRecord, SearchQuery, ComponentUsage
from components.services.search import search_components


class ComponentCatalogTests(TestCase):
    databases = {'default', 'supabase'}

    def setUp(self):
        self.client = Client()

        # Create test user
        self.user = User.objects.create_user(username='testdev', password='password123')

        # Create category hierarchy
        self.backend = Category.objects.create(name='Backend', slug='backend')
        self.auth = Category.objects.create(name='Authentication', slug='authentication', parent=self.backend)
        self.jwt_cat = Category.objects.create(name='JWT', slug='jwt', parent=self.auth)

        self.frontend = Category.objects.create(name='Frontend', slug='frontend')
        self.val_cat = Category.objects.create(name='Validation', slug='validation', parent=self.frontend)

        # Create sample components
        dummy_file = SimpleUploadedFile("sample.py", b"def test(): pass", content_type="text/plain")

        self.comp1 = Component.objects.create(
            name='JWT Authentication Module',
            description='Provides token generation and secure user login authentication mechanism.',
            component_type='CODE',
            category=self.backend,
            subcategory=self.jwt_cat,
            keywords='jwt, auth, login, security, token',
            author='Alex',
            version='1.0.0',
            file=dummy_file,
            view_count=10,
            download_count=5,
            reuse_count=2,
        )

        self.comp2 = Component.objects.create(
            name='Email Validation Utility',
            description='Utility for checking whether an email address follows a valid format.',
            component_type='CODE',
            category=self.frontend,
            subcategory=self.val_cat,
            keywords='email, validation, regex',
            author='Sarah',
            version='1.0.0',
            file=dummy_file,
            view_count=5,
            download_count=2,
            reuse_count=1,
        )

    def test_unauthenticated_user_redirected_to_login(self):
        """Unauthenticated user accessing any page must be redirected to login page."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

        response_browse = self.client.get(reverse('browse'))
        self.assertEqual(response_browse.status_code, 302)
        self.assertIn('/login/?next=/browse/', response_browse.url)

    def test_login_flow_and_redirection(self):
        """Valid login redirects user into repository."""
        response = self.client.post(reverse('login'), {
            'username': 'testdev',
            'password': 'password123',
            'next': '/components/'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/components/')

    def test_home_view(self):
        """Home view loads with correct counts and components once authenticated."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reusable Software Components")
        self.assertContains(response, "JWT Authentication Module")
        self.assertEqual(response.context['total_components'], 2)
        self.assertEqual(response.context['total_reuses'], 3)

    def test_component_list_and_filtering(self):
        """Component list displays all items and filters by type."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('component_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "JWT Authentication Module")
        self.assertContains(response, "Email Validation Utility")

        # Filter by Code
        response_code = self.client.get(reverse('component_list') + '?type=CODE')
        self.assertEqual(response_code.status_code, 200)
        self.assertEqual(response_code.context['count'], 2)

        # Filter by Design
        response_design = self.client.get(reverse('component_list') + '?type=DESIGN')
        self.assertEqual(response_design.status_code, 200)
        self.assertEqual(response_design.context['count'], 0)

    def test_component_detail_increments_views(self):
        """Viewing detail increments view count and logs usage."""
        self.client.force_login(self.user)
        initial_views = self.comp1.view_count
        response = self.client.get(reverse('component_detail', args=[self.comp1.pk]))
        self.assertEqual(response.status_code, 200)

        self.comp1.refresh_from_db()
        self.assertEqual(self.comp1.view_count, initial_views + 1)
        self.assertTrue(ComponentUsage.objects.filter(component=self.comp1, action_type='VIEW').exists())

    def test_download_increments_download_count(self):
        """Downloading component file increments download_count."""
        self.client.force_login(self.user)
        initial_downloads = self.comp1.download_count
        response = self.client.get(reverse('component_download', args=[self.comp1.pk]))
        self.assertEqual(response.status_code, 200)

        self.comp1.refresh_from_db()
        self.assertEqual(self.comp1.download_count, initial_downloads + 1)
        self.assertTrue(ComponentUsage.objects.filter(component=self.comp1, action_type='DOWNLOAD').exists())

    def test_mark_as_reused_action(self):
        """Mark as reused increases reuse_count and creates ReuseRecord."""
        self.client.force_login(self.user)
        initial_reuses = self.comp1.reuse_count
        post_data = {
            'reused_by': 'Student Team A',
            'project_name': 'E-Commerce Portal',
            'action': 'Integrated directly',
            'notes': 'Used token validation in checkout API'
        }
        response = self.client.post(reverse('component_mark_reused', args=[self.comp1.pk]), data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        self.comp1.refresh_from_db()
        self.assertEqual(self.comp1.reuse_count, initial_reuses + 1)

        record = ReuseRecord.objects.filter(component=self.comp1, project_name='E-Commerce Portal').first()
        self.assertIsNotNone(record)
        self.assertEqual(record.reused_by, 'Student Team A')

    def test_add_component_form(self):
        """Adding a component through the form creates the record."""
        self.client.force_login(self.user)
        data = {
            'name': 'Merge Sort Implementation',
            'description': 'Standard stable sorting algorithm in O(N log N).',
            'component_type': 'CODE',
            'category': self.backend.id,
            'keywords': 'sort, algorithm, divide and conquer',
            'author': 'Prof. Vance',
            'version': '1.0.0',
        }
        response = self.client.post(reverse('component_create'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)

        created_comp = Component.objects.filter(name='Merge Sort Implementation').first()
        self.assertIsNotNone(created_comp)
        self.assertEqual(created_comp.author, 'Prof. Vance')

    def test_semantic_concept_fallback_search(self):
        """
        Tests fallback search capability on conceptual queries:
        1. 'secure user login' matches 'JWT Authentication Module'
        2. 'email checker' matches 'Email Validation Utility'
        """
        res1 = search_components("secure user login")
        matched_names1 = [c.name for c in res1['results']]
        self.assertIn('JWT Authentication Module', matched_names1)

        res2 = search_components("email checker")
        matched_names2 = [c.name for c in res2['results']]
        self.assertIn('Email Validation Utility', matched_names2)

        self.assertTrue(SearchQuery.objects.filter(query_text="email checker").exists())

    def test_browse_page(self):
        """Browse view shows categories and filters components by subcategory."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('browse'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Backend")

        response_sub = self.client.get(reverse('browse') + f'?subcategory={self.jwt_cat.id}')
        self.assertEqual(response_sub.status_code, 200)
        self.assertContains(response_sub, "JWT Authentication Module")

    def test_analytics_and_query_logging(self):
        """Analytics page aggregates metrics and zero-result searches."""
        self.client.force_login(self.user)
        SearchQuery.objects.create(query_text='quantum blockchain', results_count=0)

        response = self.client.get(reverse('analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "quantum blockchain")
        self.assertGreaterEqual(response.context['zero_result_count'], 1)

    def test_reports_and_csv_export(self):
        """Reports view displays summary and CSV export responds with CSV header."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SOFTWARE COMPONENT REPOSITORY AUDIT REPORT")

        csv_response = self.client.get(reverse('export_report_csv'))
        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response['Content-Type'], 'text/csv')
        self.assertIn('Component Name', csv_response.content.decode('utf-8'))
        self.assertIn('JWT Authentication Module', csv_response.content.decode('utf-8'))
