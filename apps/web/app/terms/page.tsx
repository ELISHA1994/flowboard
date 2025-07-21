import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center">
          <Link href="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div className="flex items-center space-x-2 ml-4">
            <div className="h-8 w-8 rounded-lg bg-primary" />
            <span className="text-xl font-bold">TaskMaster</span>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="container py-8 md:py-12 max-w-4xl">
        <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>

        <div className="prose prose-gray dark:prose-invert max-w-none">
          <p className="text-lg text-muted-foreground mb-6">
            Last updated:{' '}
            {new Date().toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">1. Acceptance of Terms</h2>
            <p>
              By accessing and using TaskMaster, you accept and agree to be bound by the terms and
              provision of this agreement. If you do not agree to these terms, please do not use our
              service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">2. Use License</h2>
            <p className="mb-4">
              Subject to your compliance with these Terms, we grant you a limited, non-exclusive,
              non-transferable license to:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Access and use the services for your personal or business purposes</li>
              <li>Create, manage, and collaborate on tasks and projects</li>
              <li>Share content with team members and collaborators</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">3. User Accounts</h2>
            <p className="mb-4">To use our services, you must:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Create an account with accurate information</li>
              <li>Maintain the security of your account credentials</li>
              <li>Notify us immediately of any unauthorized access</li>
              <li>Be responsible for all activities under your account</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">4. Prohibited Uses</h2>
            <p className="mb-4">You may not use TaskMaster to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Violate any laws or regulations</li>
              <li>Infringe on intellectual property rights</li>
              <li>Transmit malicious code or viruses</li>
              <li>Harass, abuse, or harm other users</li>
              <li>Attempt to gain unauthorized access to our systems</li>
              <li>Use the service for any illegal or unauthorized purpose</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">5. Content Ownership</h2>
            <p className="mb-4">
              <strong>Your Content:</strong> You retain ownership of all content you create using
              our service. By using TaskMaster, you grant us a license to store, display, and share
              your content as necessary to provide the service.
            </p>
            <p>
              <strong>Our Content:</strong> The TaskMaster service, including its design, features,
              and functionality, is owned by us and protected by copyright, trademark, and other
              laws.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">6. Payment Terms</h2>
            <p>
              If you subscribe to a paid plan, you agree to pay all applicable fees. Subscriptions
              automatically renew unless cancelled. We reserve the right to change our pricing with
              30 days notice.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">7. Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, TaskMaster shall not be liable for any
              indirect, incidental, special, consequential, or punitive damages resulting from your
              use of or inability to use the service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">8. Termination</h2>
            <p>
              We reserve the right to terminate or suspend your account at any time for violations
              of these terms. You may also terminate your account at any time through your account
              settings.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">9. Changes to Terms</h2>
            <p>
              We may modify these terms at any time. We will notify you of any material changes via
              email or through the service. Your continued use constitutes acceptance of the
              modified terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">10. Contact Information</h2>
            <p>
              For questions about these Terms of Service, please contact us at{' '}
              <Link href="/contact" className="text-primary hover:underline">
                our contact page
              </Link>{' '}
              or email us at legal@taskmaster.com.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
