// C:\Users\Vinay\Project\frontend\cypress\e2e\profile_interaction.cy.ts

describe('User Profile Interaction', () => {
  const apiBaseUrl = Cypress.env('VITE_API_BASE_URL');

  it('allows a user to edit and save their profile bio', () => {
    // This test is correct and remains unchanged
    const testUser = { username: 'profileEditor', password: 'password123' };
    cy.testSetup('create_user', testUser);
    cy.login(testUser.username, testUser.password);
    const newBio = `This is my updated bio. Test run: ${Date.now()}`;
    cy.visit(`/profile/${testUser.username}`);
    cy.contains('p', `@${testUser.username}`).should('be.visible');
    cy.get('[data-cy="edit-profile-button"]').click();
    cy.get('[data-cy="bio-textarea"]').clear().type(newBio);
    cy.intercept('PATCH', `${apiBaseUrl}/api/profiles/${testUser.username}/`).as('updateBio');
    cy.get('[data-cy="save-profile-button"]').click();
    cy.wait('@updateBio');
    cy.get('[data-cy="profile-bio-display"]').should('have.text', newBio);
    cy.get('[data-cy="bio-textarea"]').should('not.exist');
  });

  it('allows a user to remove their profile picture', () => {
    // This test is correct and remains unchanged
    const testUser = { username: 'pictureRemover', password: 'password123', with_picture: true };
    cy.testSetup('create_user', testUser);
    cy.login(testUser.username, testUser.password);
    cy.visit(`/profile/${testUser.username}`);
    cy.get('[data-cy="profile-picture-img"]').should('exist').and('have.attr', 'src').and('include', '/media/profile_pics/');
    cy.get('[data-cy="profile-picture-container"]').click();
    cy.intercept('PATCH', `${apiBaseUrl}/api/profiles/${testUser.username}/`).as('removePicture');
    cy.get('[data-cy="remove-picture-button"]').click();
    cy.wait('@removePicture');
    cy.get('[data-cy="profile-picture-img"]').should('exist').and('have.attr', 'src').and('include', '/src/assets/images/default-avatar.svg');
    cy.get('[data-cy="profile-picture-container"]').click();
    cy.get('[data-cy="remove-picture-button"]').should('not.exist');
  });

  // --- THIS IS THE CORRECTED UPLOAD TEST ---
  it('allows a user to upload a new profile picture', () => {
    const testUser = {
      username: 'pictureUploader',
      password: 'password123',
    };
    // ARRANGE
    cy.testSetup('create_user', testUser);
    cy.login(testUser.username, testUser.password);
    cy.visit(`/profile/${testUser.username}`);
    cy.contains('p', `@${testUser.username}`).should('be.visible');

    // ACT
    cy.get('[data-cy="profile-picture-container"]').click();
    
    cy.intercept('PATCH', `${apiBaseUrl}/api/profiles/${testUser.username}/`).as('uploadPicture');

    // The selector '#picture-upload' comes from the <label for="picture-upload"> in your component
    cy.get('#picture-upload').selectFile('cypress/fixtures/test_avatar.png', { force: true });

    // ASSERT
    cy.wait('@uploadPicture').its('response.statusCode').should('eq', 200);

    // The most important assertion: Does the image on the page now point to the new uploaded file?
    cy.get('[data-cy="profile-picture-img"]')
      .should('have.attr', 'src')
      .and('include', '/media/profile_pics/test_avatar'); // We just check for the start of the file path
  });
});