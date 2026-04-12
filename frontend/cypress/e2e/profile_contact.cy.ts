// frontend/cypress/e2e/profile_contact.cy.ts

describe('User Profile Interaction', () => {
  context('"Contact" Tab Update', () => {
    const testUser = {
      username: 'contactTester',
      password: 'password123',
      email: 'contactTester@cypresstest.com',
    }

    beforeEach(() => {
      // 1. Setup fresh user
      cy.testSetup('create_user', testUser)
      // 2. Intercept the Profile API call so we can wait for it
      cy.intercept('GET', `/api/profiles/${testUser.username}/`).as('getProfile')
      // 3. Login
      cy.login(testUser.username, testUser.password)
      // 4. Navigate to profile
      cy.visit(`/profile/${testUser.username}`)
      // 5. Wait for the profile data to arrive
      cy.wait('@getProfile')
      // 6. Switch to Contact tab
      cy.contains('button', 'Contact').click()
    })

    it('allows a user to update phone number and privacy settings', () => {
      const newPhone = '8421569987'

      // --- INITIAL STATE ---
      cy.log('Verifying email is displayed and read-only')
      // Use have.value instead of not.be.empty for better reliability on inputs
      cy.get('input[type="email"]').should('be.disabled').should('have.value', testUser.email)

      // --- EDIT MODE ---
      cy.log('Step 1: Entering edit mode')
      cy.contains('button', 'Edit Details').click()

      // --- UPDATE DATA ---
      cy.log('Step 2: Updating phone and privacy dropdowns')
      cy.get('input[placeholder="No phone number added"]').clear().type(newPhone)

      // select(0) is Email Visibility, select(1) is Phone Visibility
      cy.get('select').eq(0).select('followers')
      cy.get('select').eq(1).select('self')

      // --- SAVE ---
      cy.log('Step 3: Saving changes')
      cy.intercept('PATCH', '/api/profile/contact/').as('patchContact')
      cy.contains('button', 'Save Details').click()
      cy.wait('@patchContact').its('response.statusCode').should('eq', 200)

      // --- VERIFY ---
      cy.log('Step 4: Asserting persistence')
      cy.contains('Contact information updated!').should('be.visible')

      cy.reload()
      cy.contains('button', 'Contact').click()

      // Check values persisted in the inputs
      cy.get('input')
        .filter((i, el) => (el as HTMLInputElement).value === newPhone)
        .should('exist')
      cy.get('select').eq(0).should('have.value', 'followers')
      cy.get('select').eq(1).should('have.value', 'self')
    })

    it('should reset form values when "Cancel" is clicked', () => {
      cy.contains('button', 'Edit Details').click()
      cy.get('input').last().clear().type('9999999999')
      cy.contains('button', 'Cancel').click()

      cy.get('input').last().should('be.disabled')
      cy.get('input').last().should('not.have.value', '9999999999')
    })
  })
})
