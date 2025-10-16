// C:\Users\Vinay\Project\frontend\cypress\e2e\profile_interaction.cy.ts

describe('User Profile Interaction', () => {
  const apiBaseUrl = Cypress.env('VITE_API_BASE_URL')

  it('allows a user to edit their profile summary via the modal', () => {
    // This test is unrelated to the picture sync and remains unchanged.
    const testUser = { username: 'profileEditor', password: 'password123' }
    cy.testSetup('create_user', testUser)
    cy.login(testUser.username, testUser.password)

    const newDisplayName = `Test User ${Date.now()}`
    const newHeadline = 'Cypress Test Specialist'

    cy.visit(`/profile/${testUser.username}`)
    cy.contains('p', `@${testUser.username}`).should('be.visible')

    cy.get('[aria-label="Edit profile summary"]').click()
    cy.contains('h3', 'Edit Profile Summary').should('be.visible')

    cy.get('input#display_name').clear().type(newDisplayName)
    cy.get('input#headline').clear().type(newHeadline)

    cy.intercept('PATCH', `${apiBaseUrl}/api/profiles/${testUser.username}/`).as('updateProfile')
    cy.contains('button', 'Save Changes').click()

    cy.wait('@updateProfile')

    cy.get('h1').should('contain.text', newDisplayName)
    cy.contains('p', newHeadline).should('be.visible')
  })

  // --- ENHANCED TEST FOR PICTURE UPLOAD AND STATE SYNC ---
  it('updates the profile picture on the card, navbar, and in posts after upload', () => {
    const testUser = { username: 'pictureUploader', password: 'password123' }
    // SETUP: Create a user and a post by that user to test synchronization
    cy.testSetup('create_user_and_post', { user: testUser, post: { content: 'My first post!' } })
    cy.login(testUser.username, testUser.password)
    cy.visit(`/profile/${testUser.username}`)

    // ASSERT INITIAL STATE: All avatars use the default (src does not contain '/media/')
    cy.get('[data-cy="profile-picture-img"]').should('not.have.attr', 'src', '*/media/*')
    cy.get('[data-cy="navbar-avatar-main"]').should('not.have.attr', 'src', '*/media/*')
    cy.get('[data-cy="post-author-avatar"]').should('not.have.attr', 'src', '*/media/*')

    // ACTION: Upload a new picture
    cy.get('[data-cy="profile-picture-container"]').click()
    cy.intercept('PATCH', `${apiBaseUrl}/api/profiles/${testUser.username}/`).as('uploadPicture')
    cy.get('input#picture-upload').selectFile('cypress/fixtures/test_avatar.png', { force: true })
    cy.wait('@uploadPicture')

    // ASSERT FINAL STATE: All three avatar locations now show the new picture
    const newPicturePath = '/media/profile_pics/test_avatar'
    cy.get('[data-cy="profile-picture-img"]')
      .should('have.attr', 'src')
      .and('include', newPicturePath)
    cy.get('[data-cy="navbar-avatar-main"]')
      .should('have.attr', 'src')
      .and('include', newPicturePath)
    cy.get('[data-cy="post-author-avatar"]')
      .should('have.attr', 'src')
      .and('include', newPicturePath)

    // Also check the dropdown avatar for completeness
    cy.get('[data-cy="profile-menu-button"]').click()
    cy.get('[data-cy="navbar-avatar-dropdown"]')
      .should('have.attr', 'src')
      .and('include', newPicturePath)
  })

  // --- ENHANCED TEST FOR PICTURE REMOVAL AND STATE SYNC ---
  it('reverts the profile picture on the card, navbar, and in posts after removal', () => {
    const testUser = { username: 'pictureRemover', password: 'password123' }
    // SETUP: Create a user WITH a picture and a post
    cy.testSetup('create_user_and_post', {
      user: { ...testUser, with_picture: true },
      post: { content: 'A post with a picture!' },
    })
    cy.login(testUser.username, testUser.password)
    cy.visit(`/profile/${testUser.username}`)

    // ASSERT INITIAL STATE: All avatars show the initial picture
    cy.get('[data-cy="profile-picture-img"]')
      .should('have.attr', 'src')
      .and('include', '/media/profile_pics/')
    cy.get('[data-cy="navbar-avatar-main"]')
      .should('have.attr', 'src')
      .and('include', '/media/profile_pics/')
    cy.get('[data-cy="post-author-avatar"]')
      .should('have.attr', 'src')
      .and('include', '/media/profile_pics/')

    // ACTION: Remove the picture
    cy.get('[data-cy="profile-picture-container"]').click()
    cy.intercept('PATCH', `${apiBaseUrl}/api/profiles/${testUser.username}/`).as('removePicture')
    cy.get('[data-cy="remove-picture-button"]').click()
    cy.wait('@removePicture')

    // ASSERT FINAL STATE: All three avatar locations have reverted to the default
    cy.get('[data-cy="profile-picture-img"]').should('not.have.attr', 'src', '*/media/*')
    cy.get('[data-cy="navbar-avatar-main"]').should('not.have.attr', 'src', '*/media/*')
    cy.get('[data-cy="post-author-avatar"]').should('not.have.attr', 'src', '*/media/*')

    // Also check the dropdown avatar for completeness
    cy.get('[data-cy="profile-menu-button"]').click()
    cy.get('[data-cy="navbar-avatar-dropdown"]').should('not.have.attr', 'src', '*/media/*')
  })
})
