import { Link } from 'react-router-dom'

function PrivacyPolicy() {
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
          <h1 className="text-3xl font-bold text-foreground mb-2">Privacy Policy</h1>
          <p className="text-sm text-muted-foreground mb-8">Last updated: November 30, 2025</p>

          <div className="prose prose-slate dark:prose-invert max-w-none">
            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">1. Introduction</h2>
              <p className="text-foreground/90 mb-4">
                DocMCP is an open source project that respects your privacy. This policy explains
                how we handle information when you use our service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">2. Information We Collect</h2>
              <p className="text-foreground/90 mb-4">
                When you use DocMCP, we may collect:
              </p>
              <ul className="list-disc pl-6 mb-4 text-foreground/90 space-y-2">
                <li>
                  <strong>Account Information:</strong> Email address and password (if using local authentication)
                  or OAuth profile information (if using Google authentication)
                </li>
                <li>
                  <strong>Content Data:</strong> Documents, projects, and other content you create or upload
                </li>
                <li>
                  <strong>Usage Data:</strong> Information about how you interact with the service
                </li>
                <li>
                  <strong>Technical Data:</strong> Browser type, IP address, device information, and cookies
                </li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">3. How We Use Your Information</h2>
              <p className="text-foreground/90 mb-4">
                We use the collected information to:
              </p>
              <ul className="list-disc pl-6 mb-4 text-foreground/90 space-y-2">
                <li>Provide and maintain the service</li>
                <li>Authenticate and authorize users</li>
                <li>Store and manage your content</li>
                <li>Improve and optimize the service</li>
                <li>Ensure security and prevent abuse</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">4. Data Storage and Security</h2>
              <p className="text-foreground/90 mb-4">
                Your data is stored securely. However, as this is an open source project provided
                "as is," we cannot guarantee absolute security. We implement reasonable security
                measures but cannot ensure complete protection against all security threats.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">5. Data Sharing</h2>
              <p className="text-foreground/90 mb-4">
                We do not sell, trade, or rent your personal information to third parties. We may share
                information only in the following circumstances:
              </p>
              <ul className="list-disc pl-6 mb-4 text-foreground/90 space-y-2">
                <li>With your explicit consent</li>
                <li>When required by law or to protect rights and safety</li>
                <li>With service providers necessary to operate the service (e.g., hosting, authentication)</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">6. Third-Party Services</h2>
              <p className="text-foreground/90 mb-4">
                If you choose to authenticate via Google OAuth, your interaction with Google is
                governed by Google's privacy policy. We only receive basic profile information
                necessary for authentication.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">7. Cookies</h2>
              <p className="text-foreground/90 mb-4">
                We use cookies and similar technologies to maintain your session and improve your
                experience. You can control cookie preferences through your browser settings, though
                disabling cookies may affect service functionality.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">8. Data Retention</h2>
              <p className="text-foreground/90 mb-4">
                We retain your data for as long as your account is active or as needed to provide
                the service. You may delete your content at any time through the service interface.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">9. Your Rights</h2>
              <p className="text-foreground/90 mb-4">
                Depending on your location, you may have rights regarding your personal data, including:
              </p>
              <ul className="list-disc pl-6 mb-4 text-foreground/90 space-y-2">
                <li>Access to your personal data</li>
                <li>Correction of inaccurate data</li>
                <li>Deletion of your data</li>
                <li>Export of your data</li>
                <li>Objection to data processing</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">10. Children's Privacy</h2>
              <p className="text-foreground/90 mb-4">
                This service is not intended for children under 13 years of age. We do not knowingly
                collect personal information from children under 13.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">11. Open Source Nature</h2>
              <p className="text-foreground/90 mb-4">
                As an open source project, the code is publicly available. While we strive to protect
                your data, anyone can review the source code and potentially deploy their own instance.
                Each deployment may have different privacy practices.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">12. Changes to This Policy</h2>
              <p className="text-foreground/90 mb-4">
                We may update this privacy policy from time to time. Changes will be posted on this
                page with an updated revision date. Continued use of the service after changes
                constitutes acceptance of the updated policy.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">13. Contact</h2>
              <p className="text-foreground/90 mb-4">
                For questions about this privacy policy or your data, please contact the project
                maintainers through the project's repository or community channels.
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PrivacyPolicy
