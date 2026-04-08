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

        // Safely extract the URL whether it is http or https
        const resetUrlMatch = emailBody.match(/https?:\/\/[^\s"']+/)
        expect(resetUrlMatch).to.not.be.null

        // Use the matched string
        const resetUrl = resetUrlMatch![0]

        // 4. BULLETPROOF ROUTING: Extract just the UID and TOKEN
        // Example: https://...:8000/password-reset/5on/d6mdep-20bf.../
        const urlParts = resetUrl.split('/').filter(Boolean)
        const token = urlParts.pop() // Gets the last part (Token)
        const uid = urlParts.pop() // Gets the second to last part (UID)

        // 5. Visit the correct Frontend Vue Route directly (Port 5173)
        cy.visit(`/auth/reset-password/${uid}/${token}/`)

        // 6. Assert we landed on the correct frontend page
        cy.get('h2').should('contain', 'Choose a New Password')
        cy.get('#new_password1').should('be.visible')
      })
    })
  })
})
