import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight, CheckCircle, Users, BarChart3, Zap } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded-lg bg-primary" />
            <span className="text-xl font-bold">TaskMaster</span>
          </div>
          <nav className="flex items-center space-x-6 text-sm font-medium">
            <Link href="#features" className="text-muted-foreground hover:text-foreground">
              Features
            </Link>
            <Link href="#pricing" className="text-muted-foreground hover:text-foreground">
              Pricing
            </Link>
            <Link href="#about" className="text-muted-foreground hover:text-foreground">
              About
            </Link>
            <Link href="/dashboard">
              <Button variant="default" size="sm">
                Dashboard
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container grid lg:grid-cols-2 gap-8 py-20">
        <div className="flex flex-col justify-center space-y-4">
          <div className="space-y-2">
            <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none">
              Modern Task Management for Teams
            </h1>
            <p className="max-w-[600px] text-muted-foreground md:text-xl">
              Streamline your workflow with our powerful task management system. Built for teams who
              want to move fast and stay organized.
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Link href="/dashboard">
              <Button size="lg" className="w-full sm:w-auto">
                Get Started Free
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="#features">
              <Button size="lg" variant="outline" className="w-full sm:w-auto">
                Learn More
              </Button>
            </Link>
          </div>
        </div>
        <div className="flex items-center justify-center">
          <div className="relative w-full max-w-lg">
            <div className="absolute -inset-1 rounded-lg bg-gradient-to-r from-primary to-accent opacity-75 blur"></div>
            <div className="relative rounded-lg bg-background p-8">
              <div className="space-y-4">
                <div className="h-4 w-3/4 rounded bg-muted"></div>
                <div className="h-4 w-1/2 rounded bg-muted"></div>
                <div className="space-y-2">
                  <div className="h-10 rounded bg-muted/50"></div>
                  <div className="h-10 rounded bg-muted/50"></div>
                  <div className="h-10 rounded bg-muted/50"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="container py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">
            Everything you need to stay productive
          </h2>
          <p className="mt-4 text-muted-foreground text-lg">
            Powerful features designed for modern teams
          </p>
        </div>
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-lg border bg-card p-8">
            <CheckCircle className="h-12 w-12 text-primary mb-4" />
            <h3 className="text-xl font-bold mb-2">Task Management</h3>
            <p className="text-muted-foreground">
              Create, assign, and track tasks with ease. Multiple views including Kanban, List, and
              Calendar.
            </p>
          </div>
          <div className="rounded-lg border bg-card p-8">
            <Users className="h-12 w-12 text-primary mb-4" />
            <h3 className="text-xl font-bold mb-2">Team Collaboration</h3>
            <p className="text-muted-foreground">
              Real-time updates, comments, and mentions. Work together seamlessly.
            </p>
          </div>
          <div className="rounded-lg border bg-card p-8">
            <BarChart3 className="h-12 w-12 text-primary mb-4" />
            <h3 className="text-xl font-bold mb-2">Analytics & Insights</h3>
            <p className="text-muted-foreground">
              Track productivity, visualize progress, and make data-driven decisions.
            </p>
          </div>
          <div className="rounded-lg border bg-card p-8">
            <Zap className="h-12 w-12 text-primary mb-4" />
            <h3 className="text-xl font-bold mb-2">Lightning Fast</h3>
            <p className="text-muted-foreground">
              Optimized for speed with keyboard shortcuts and instant search.
            </p>
          </div>
          <div className="rounded-lg border bg-card p-8">
            <CheckCircle className="h-12 w-12 text-primary mb-4" />
            <h3 className="text-xl font-bold mb-2">Integrations</h3>
            <p className="text-muted-foreground">
              Connect with your favorite tools. GitHub, Slack, Calendar, and more.
            </p>
          </div>
          <div className="rounded-lg border bg-card p-8">
            <Users className="h-12 w-12 text-primary mb-4" />
            <h3 className="text-xl font-bold mb-2">Advanced Features</h3>
            <p className="text-muted-foreground">
              Recurring tasks, dependencies, custom fields, and automation.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container py-20">
        <div className="rounded-lg bg-primary px-8 py-12 text-center text-primary-foreground">
          <h2 className="text-3xl font-bold mb-4">Ready to get started?</h2>
          <p className="mb-8 text-lg opacity-90">
            Join thousands of teams already using TaskMaster
          </p>
          <Link href="/dashboard">
            <Button size="lg" variant="secondary">
              Start Free Trial
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="container flex flex-col items-center justify-between gap-4 md:flex-row">
          <p className="text-sm text-muted-foreground">© 2024 TaskMaster. All rights reserved.</p>
          <nav className="flex gap-4 text-sm text-muted-foreground">
            <Link href="/privacy" className="hover:text-foreground">
              Privacy
            </Link>
            <Link href="/terms" className="hover:text-foreground">
              Terms
            </Link>
            <Link href="/contact" className="hover:text-foreground">
              Contact
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
