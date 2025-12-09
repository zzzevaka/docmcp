import { Link } from 'react-router-dom'

function TermsOfService() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="mb-8">
          <Link
            to="/"
            className="text-primary hover:text-primary/80 text-sm font-medium"
          >
            ← Back
          </Link>
        </div>

        <div className="bg-card border border-border rounded-lg shadow-sm p-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Terms of Service</h1>
          <p className="text-sm text-muted-foreground mb-8">Last updated: November 30, 2025</p>

          <div className="prose prose-slate dark:prose-invert max-w-none">
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">1. Introduction</h2>
              <p className="text-foreground/90 mb-4">
                Welcome to DocuMur. This is an open source project provided "as is" without any warranties.
                By using this service, you agree to these terms.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">2. Open Source</h2>
              <p className="text-foreground/90 mb-4">
                DocuMur is an open source project. The source code is available for review, modification,
                and distribution according to the project's license. This is a community-driven project
                with no commercial intent.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">3. Use of Service</h2>
              <p className="text-foreground/90 mb-4">
                You may use this service for lawful purposes only. You agree not to:
              </p>
              <ul className="list-disc pl-6 mb-4 text-foreground/90 space-y-2">
                <li>Violate any laws or regulations</li>
                <li>Infringe on others' intellectual property rights</li>
                <li>Upload malicious content or attempt to compromise the service</li>
                <li>Use the service to harass, abuse, or harm others</li>
                <li>Attempt to gain unauthorized access to the service or related systems</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">4. User Content</h2>
              <p className="text-foreground/90 mb-4">
                You retain ownership of any content you create or upload to the service. You are responsible
                for the content you post and must have the necessary rights to share it.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">5. No Warranty</h2>
              <p className="text-foreground/90 mb-4">
                This service is provided "as is" without warranty of any kind, express or implied.
                We do not guarantee that the service will be uninterrupted, secure, or error-free.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">6. Limitation of Liability</h2>
              <p className="text-foreground/90 mb-4">
                To the maximum extent permitted by law, the service providers shall not be liable for any
                indirect, incidental, special, consequential, or punitive damages resulting from your use
                or inability to use the service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">7. Data and Privacy</h2>
              <p className="text-foreground/90 mb-4">
                Your use of the service is also governed by our{' '}
                <Link to="/privacy-policy" className="text-primary hover:text-primary/80 underline">
                  Privacy Policy
                </Link>
                .
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">8. Changes to Terms</h2>
              <p className="text-foreground/90 mb-4">
                We reserve the right to modify these terms at any time. Changes will be effective
                immediately upon posting. Your continued use of the service constitutes acceptance
                of the modified terms.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">9. Termination</h2>
              <p className="text-foreground/90 mb-4">
                We reserve the right to terminate or suspend access to the service at any time,
                without prior notice, for any reason, including breach of these terms.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">10. Contact</h2>
              <p className="text-foreground/90 mb-4">
                For questions about these terms, please contact the project maintainers through
                the project's repository or community channels.
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TermsOfService
