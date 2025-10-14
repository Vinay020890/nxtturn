// C:\Users\Vinay\Project\frontend\cypress\e2e\profile_interaction.cy.ts

describe('User Profile Interaction', () => {
  // FIX: Moved the constant here so all tests in the block can access it.
  const apiBaseUrl = Cypress.env('VITE_API_BASE_URL')

  it('allows a user to edit and save their profile bio using in-place controls', () => {
    // ARRANGE: Create user, log in, define new bio
    const testUser = { username: 'profileEditor', password: 'password123' }
    cy.testSetup('create_user', testUser)
    cy.login(testUser.username, testUser.password)
    const newBio = `This is my updated bio. Test run: ${Date.now()}`
    cy.visit(`/profile/${testUser.username}`)
    cy.contains('p', `@${testUser.username}`).should('be.visible')

    // ACT: Perform the new edit workflow
    cy.get('[data-cy="edit-bio-button"]').click({ force: true })
    cy.get('[data-cy="bio-textarea"]').clear().type(newBio)
    cy.intercept('PATCH', `${apiBaseUrl}/api/profiles/${testUser.username}/`).as('updateBio')
    cy.get('[data-cy="save-bio-button"]').click()

    // ASSERT: Wait for the API call and verify the UI updates
    cy.wait('@updateBio')
    cy.get('[data-cy="profile-bio-display"]').should('have.text', newBio)
    cy.get('[data-cy="bio-textarea"]').should('not.exist')
  })

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
      .and('include', '/src/assets/images/default-avatar.svg')
    cy.get('[data-cy="profile-picture-container"]').click()
    cy.get('[data-cy="remove-picture-button"]').should('not.exist')
  })

  it('allows a user to upload a new profile picture', () => {
    const testUser = {
      username: 'pictureUploader',
      password: 'password123',
    }
    cy.testSetup('create_user', testUser)
    cy.login(testUser.username, testUser.password)
    cy.visit(`/profile/${testUser.username}`)
    cy.contains('p', `@${testUser.username}`).should('be.visible')
    cy.get('[data-cy="profile-picture-container"]').click()

    // FIX: Corrected the 'apiBase-url' typo to 'apiBaseUrl'
    cy.intercept('PATCH', `${apiBaseUrl}/api/profiles/${testUser.username}/`).as('uploadPicture')

    cy.get('#picture-upload').selectFile('cypress/fixtures/test_avatar.png', { force: true })
    cy.wait('@uploadPicture').its('response.statusCode').should('eq', 200)
    cy.get('[data-cy="profile-picture-img"]')
      .should('have.attr', 'src')
      .and('include', '/media/profile_pics/test_avatar')
  })
})
