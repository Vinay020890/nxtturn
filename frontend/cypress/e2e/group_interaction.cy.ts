// C:\Users\Vinay\Project\frontend\cypress\e2e/group_interaction.cy.ts

describe('Group Creation and Interaction', () => {

  it('a user can create a new public group', () => {
    const testId = Date.now();
    const creatorUsername = `creator_${testId}`;
    const groupName = `Public Group ${testId}`;

    cy.testSetup('create_user', {
      email: `${creatorUsername}@test.com`,
      username: creatorUsername,
      password: 'password',
    }).then(() => {
      cy.login(creatorUsername, 'password');
      cy.visit('/groups');
      cy.get('[data-cy="create-group-button"]').click();
      cy.get('[data-cy="group-name-input"]').type(groupName);
      cy.get('[data-cy="group-description-input"]').type('A test description.');
      cy.get('input[value="public"]').check();
      cy.get('[data-cy="create-group-submit-button"]').click();
      cy.url().should('include', `/groups/public-group-${testId}`);
      cy.get('[data-cy="group-name-header"]').should('be.visible');
    });
  });

  it('a user can create a second group with the same name as an existing one', () => {
    const testId = Date.now();
    const creatorUsername = `creator_${testId}`;
    const sharedGroupName = `Shared Name Group ${testId}`;
    
    cy.testSetup('create_user', {
      email: `${creatorUsername}@test.com`,
      username: creatorUsername,
      password: 'password',
    }).then(() => {
      cy.login(creatorUsername, 'password');

      cy.visit('/groups');
      cy.get('[data-cy="create-group-button"]').click();
      cy.get('[data-cy="group-name-input"]').type(sharedGroupName);
      cy.get('[data-cy="group-description-input"]').type('First group.');
      cy.get('[data-cy="create-group-submit-button"]').click();
      cy.url().should('not.eq', `${Cypress.config().baseUrl}/groups`).as('firstGroupUrl');

      cy.visit('/groups');
      cy.get('[data-cy="create-group-button"]').click();
      cy.get('[data-cy="group-name-input"]').type(sharedGroupName);
      cy.get('[data-cy="group-description-input"]').type('Second group.');
      cy.get('[data-cy="create-group-submit-button"]').click();
      cy.get('[data-cy="group-name-header"]').should('be.visible');
      cy.url().as('secondGroupUrl');

      cy.get('@firstGroupUrl').then((firstUrl) => {
        cy.get('@secondGroupUrl').should('not.eq', firstUrl);
      });
    });
  });

  it('a user can join and then leave a public group', () => {
    const testId = Date.now();
    const creatorUsername = `creator_${testId}`;
    const joinerUsername = `joiner_${testId}`;
    const groupName = `Join-Leave Group ${testId}`;
    const groupSlug = `join-leave-group-${testId}`;

    cy.testSetup('create_user', {
      email: `${creatorUsername}@test.com`,
      username: creatorUsername,
      password: 'password',
    }).then(() => {
      cy.testSetup('create_user', {
        email: `${joinerUsername}@test.com`,
        username: joinerUsername,
        password: 'password',
      });
    }).then(() => {
      // Part 1: Creator makes the group
      cy.login(creatorUsername, 'password');
      cy.visit('/groups');
      cy.get('[data-cy="create-group-button"]').click();
      cy.get('[data-cy="group-name-input"]').type(groupName);
      cy.get('[data-cy="group-description-input"]').type('A group for testing join/leave.');
      cy.get('[data-cy="create-group-submit-button"]').click();
      cy.url().should('include', `/groups/${groupSlug}`).as('groupPageUrl');
      cy.logout();

      // Part 2: Joiner interacts with the group
      cy.login(joinerUsername, 'password');
      
      cy.intercept('GET', '**/api/auth/user/').as('getUser');
      cy.intercept('GET', `**/api/groups/${groupSlug}/`).as('getGroupDetails');
      cy.get('@groupPageUrl').then(url => {
        cy.visit(url as unknown as string);
      });
      cy.wait(['@getUser', '@getGroupDetails']);

      // Join the group
      cy.intercept('POST', `**/api/groups/${groupSlug}/membership/`).as('joinGroup');
      cy.get('[data-cy="group-membership-button"]').should('contain.text', 'Join Group').click();
      cy.wait('@joinGroup');
      
      // Assert the joined state
      cy.get('[data-cy="group-membership-button"]').should('contain.text', 'Leave Group');
      // CORRECTED: Use the selector that actually exists in the component.
      cy.get('[data-cy="create-post-input"]').should('be.visible');

      // Leave the group
      cy.intercept('DELETE', `**/api/groups/${groupSlug}/membership/`).as('leaveGroup');
      cy.get('[data-cy="group-membership-button"]').click();
      cy.wait('@leaveGroup');

      // Assert the left state
      cy.get('[data-cy="group-membership-button"]').should('contain.text', 'Join Group');
      // CORRECTED: Check that the input is no longer in the DOM.
      cy.get('[data-cy="create-post-input"]').should('not.exist');
    });
  });
});