// C:\Users\Vinay\Project\frontend\cypress\e2e\password-reset.cy.ts

describe('Password Reset Flow', () => {
  const resetUser = {
    username: `reset_user_${Date.now()}`,
    email: `reset_${Date.now()}@cypresstest.com`,
    password: 'oldpassword123',
  }

  before(() => {
    // Uses your existing custom command to seed the database
    cy.testSetup('create_user', resetUser)
  })

  context('on a standard viewport', () => {
    beforeEach(() => {
      cy.viewport('macbook-15')
    })

    it('successfully requests a reset, intercepts the email, and loads the confirm page', () => {
      // 1. Request the reset
      cy.visit('/auth/forgot-password')
      cy.get('h2').should('contain', 'Forgot Your Password?')

      cy.get('#email').type(resetUser.email)
      cy.get('button[type="submit"]').click()

      // 2. Confirm the frontend shows success
      cy.get('.bg-green-100').should('be.visible').and('contain.text', 'Success')

      // 3. Intercept the email from the backend using your existing test utility
      cy.testSetup('get_last_email').then((response) => {
        const emailBody = response.body.data.body

        // Use a Regular Expression to extract the http://... link from the text
        const resetUrlMatch = emailBody.match(/http:\/\/[^\s]+/)
        expect(resetUrlMatch).to.not.be.null

        const resetUrl = resetUrlMatch[0]

        // 4. Visit the intercepted link
        cy.visit(resetUrl)

        // 5. Assert we landed on the correct frontend page
        cy.get('h2').should('contain', 'Choose a New Password')
        cy.get('#new_password1').should('be.visible')
      })
    })
  })
})
