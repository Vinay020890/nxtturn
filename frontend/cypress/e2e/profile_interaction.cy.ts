// C:\Users\Vinay\Project\frontend\cypress\e2e\profile_interaction.cy.ts

describe('User Profile Interaction', () => {
  const apiBaseUrl = Cypress.env('VITE_API_BASE_URL')

  // UPDATED: This test now checks the full modal workflow for editing identity.
  it('allows a user to edit their profile summary via the modal', () => {
    // ARRANGE
    const testUser = { username: 'profileEditor', password: 'password123' }
    cy.testSetup('create_user', testUser)
    cy.login(testUser.username, testUser.password)

    const newDisplayName = `Test User ${Date.now()}`
    const newHeadline = 'Cypress Test Specialist'

    cy.visit(`/profile/${testUser.username}`)
    cy.contains('p', `@${testUser.username}`).should('be.visible')

    // ACT
    // 1. Open the "Edit Profile Summary" modal from the ProfileCard
    cy.get('[aria-label="Edit profile summary"]').click()
    cy.contains('h3', 'Edit Profile Summary').should('be.visible')

    // 2. Fill in the form inside the modal
    cy.get('input#display_name').clear().type(newDisplayName)
    cy.get('input#headline').clear().type(newHeadline)

    // 3. Intercept the API call and save
    cy.intercept('PATCH', `${apiBaseUrl}/api/profiles/${testUser.username}/`).as('updateProfile')
    cy.contains('button', 'Save Changes').click()

    // ASSERT
    cy.wait('@updateProfile')

    // 4. Verify the UI updated on the ProfileCard
    cy.get('h1').should('contain.text', newDisplayName)
    cy.contains('p', newHeadline).should('be.visible')
  })

  // This test is already passing, no changes needed, but keeping for completeness.
  it('allows a user to remove their profile picture', () => {
    const testUser = { username: 'pictureRemover', password: 'password123', with_picture: true }
    cy.testSetup('create_user', testUser)
    cy.login(testUser.username, testUser.password)
    cy.visit(`/profile/${testUser.username}`)

    cy.get('[data-cy="profile-picture-img"]')
      .should('exist')
      .and('have.attr', 'src')
      .and('include', '/media/profile_pics/')
    cy.get('[data-cy="profile-picture-container"]').click()
    cy.intercept('PATCH', `${apiBaseUrl}/api/profiles/${testUser.username}/`).as('removePicture')
    cy.get('[data-cy="remove-picture-button"]').click()
    cy.wait('@removePicture')
    cy.get('[data-cy="profile-picture-img"]')
      .should('exist')
      .and('have.attr', 'src')
      .and('not.include', '/media/profile_pics/')
    cy.get('[data-cy="profile-picture-container"]').click()
    cy.get('[data-cy="remove-picture-button"]').should('not.exist')
  })

  // This test is already passing, no changes needed, but keeping for completeness.
  it('allows a user to upload a new profile picture', () => {
    const testUser = { username: 'pictureUploader', password: 'password123' }
    cy.testSetup('create_user', testUser)
    cy.login(testUser.username, testUser.password)
    cy.visit(`/profile/${testUser.username}`)
    cy.contains('p', `@${testUser.username}`).should('be.visible')
    cy.get('[data-cy="profile-picture-container"]').click()
    cy.intercept('PATCH', `${apiBaseUrl}/api/profiles/${testUser.username}/`).as('uploadPicture')
    cy.get('input#picture-upload').selectFile('cypress/fixtures/test_avatar.png', { force: true })
    cy.wait('@uploadPicture').its('response.statusCode').should('eq', 200)
    cy.get('[data-cy="profile-picture-img"]')
      .should('have.attr', 'src')
      .and('include', '/media/profile_pics/test_avatar')
  })
})
