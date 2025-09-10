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

      cy.intercept('POST', `**/api/groups/${groupSlug}/membership/`).as('joinGroup');
      cy.get('[data-cy="group-membership-button"]').should('contain.text', 'Join Group').click();
      cy.wait('@joinGroup');
      
      cy.get('[data-cy="group-membership-button"]').should('not.exist');
      cy.get('[data-cy="group-options-button"]').should('be.visible').click();
      cy.get('[data-cy="leave-group-button"]').should('be.visible');
      cy.get('[data-cy="create-post-input"]').should('be.visible');

      cy.intercept('DELETE', `**/api/groups/${groupSlug}/membership/`).as('leaveGroup');
      cy.get('[data-cy="leave-group-button"]').click();
      cy.wait('@leaveGroup');

      cy.get('[data-cy="group-membership-button"]').should('contain.text', 'Join Group');
      cy.get('[data-cy="create-post-input"]').should('not.exist');
    });
  });

  it('a non-member can see posts in a public group', () => {
    const testId = Date.now();
    const creatorUsername = `creator_${testId}`;
    const viewerUsername = `viewer_${testId}`;
    const groupName = `Visibility Test Group ${testId}`;
    const groupSlug = `visibility-test-group-${testId}`;
    const postContent = `This is a public post that everyone should see. ID: ${testId}`;

    cy.testSetup('create_user', {
      email: `${creatorUsername}@test.com`,
      username: creatorUsername,
      password: 'password',
    }).then(() => {
      cy.testSetup('create_user', {
        email: `${viewerUsername}@test.com`,
        username: viewerUsername,
        password: 'password',
      });
    }).then(() => {
      // Part 1: Creator makes a group and a post inside it
      cy.login(creatorUsername, 'password');
      cy.visit('/groups');
      cy.get('[data-cy="create-group-button"]').click();
      cy.get('[data-cy="group-name-input"]').type(groupName);
      cy.get('[data-cy="group-description-input"]').type('A group for testing visibility.');
      cy.get('[data-cy="create-group-submit-button"]').click();
      cy.url().should('include', `/groups/${groupSlug}`).as('groupPageUrl');

      cy.intercept('POST', '**/api/posts/').as('createPost');
      cy.get('[data-cy="create-post-input"]').type(postContent);
      cy.get('[data-cy="create-post-submit-button"]').click();
      cy.wait('@createPost');
      cy.logout();

      // Part 2: Viewer visits the group page
      cy.login(viewerUsername, 'password');
      cy.intercept('GET', `**/api/groups/${groupSlug}/`).as('getGroupDetails');
      cy.get('@groupPageUrl').then(url => {
        cy.visit(url as unknown as string);
      });
      cy.wait('@getGroupDetails');

      cy.contains(postContent).should('be.visible');
      cy.get('[data-cy="group-membership-button"]').should('contain.text', 'Join Group');
    });
  });

  it('the creator and a regular member can both post in the group', () => {
    const testId = Date.now();
    const creatorUsername = `creator_${testId}`;
    const memberUsername = `member_${testId}`;
    const groupName = `Posting Permissions Test Group ${testId}`;
    const groupSlug = `posting-permissions-test-group-${testId}`;
    const creatorPost = `This is the creator's original post. ID: ${testId}`;
    const memberPost = `This is a post from a regular member. ID: ${testId}`;

    cy.testSetup('create_user', {
      email: `${creatorUsername}@test.com`,
      username: creatorUsername,
      password: 'password',
    }).then(() => {
      cy.testSetup('create_user', {
        email: `${memberUsername}@test.com`,
        username: memberUsername,
        password: 'password',
      });
    }).then(() => {
      // Part 1: Creator makes the group and their post
      cy.login(creatorUsername, 'password');
      cy.visit('/groups');
      cy.get('[data-cy="create-group-button"]').click();
      cy.get('[data-cy="group-name-input"]').type(groupName);
      cy.get('[data-cy="group-description-input"]').type('A group for testing posting.');
      cy.get('[data-cy="create-group-submit-button"]').click();
      cy.url().should('include', `/groups/${groupSlug}`).as('groupPageUrl');
      cy.get('[data-cy="group-name-header"]').should('be.visible');

      cy.intercept('POST', '**/api/posts/').as('createPost');
      cy.get('[data-cy="create-post-input"]').type(creatorPost);
      cy.get('[data-cy="create-post-submit-button"]').click();
      cy.wait('@createPost');
      cy.contains(creatorPost).should('be.visible');
      cy.logout();

      // Part 2: Regular member joins and makes their post
      cy.login(memberUsername, 'password');
      cy.intercept('GET', `**/api/groups/${groupSlug}/`).as('getGroupDetails');
      cy.get('@groupPageUrl').then(url => {
        cy.visit(url as unknown as string);
      });
      cy.wait('@getGroupDetails');

      cy.intercept('POST', `**/api/groups/${groupSlug}/membership/`).as('joinGroup');
      cy.get('[data-cy="group-membership-button"]').click();
      cy.wait('@joinGroup');

      cy.get('[data-cy="create-post-input"]').type(memberPost);
      cy.get('[data-cy="create-post-submit-button"]').click();
      cy.wait('@createPost');
      cy.contains(memberPost).should('be.visible');
      cy.contains(creatorPost).should('be.visible');
    });
  });

  it('a post made in a public group appears on the group, profile, and home feeds', () => {
    const testId = Date.now();
    const creatorUsername = `creator_${testId}`;
    const followerUsername = `follower_${testId}`;
    const groupName = `Feed Propagation Test Group ${testId}`;
    const groupSlug = `feed-propagation-test-group-${testId}`;
    const postContent = `This post should propagate to all feeds. ID: ${testId}`;

    cy.testSetup('create_user', {
      email: `${creatorUsername}@test.com`,
      username: creatorUsername,
      password: 'password',
    }).then(() => {
      cy.testSetup('create_user', {
        email: `${followerUsername}@test.com`,
        username: followerUsername,
        password: 'password',
      });
    }).then(() => {
      cy.testSetup('create_follow', { follower: followerUsername, following: creatorUsername });
    }).then(() => {
      // Part 1: Creator makes the group and the post
      cy.login(creatorUsername, 'password');
      cy.visit('/groups');
      cy.get('[data-cy="create-group-button"]').click();
      cy.get('[data-cy="group-name-input"]').type(groupName);
      cy.get('[data-cy="group-description-input"]').type('A group for testing feed propagation.');
      cy.get('[data-cy="create-group-submit-button"]').click();
      cy.url().should('include', `/groups/${groupSlug}`);
      cy.get('[data-cy="group-name-header"]').should('be.visible');

      cy.intercept('POST', '**/api/posts/').as('createPost');
      cy.get('[data-cy="create-post-input"]').type(postContent);
      cy.get('[data-cy="create-post-submit-button"]').click();
      cy.wait('@createPost');

      cy.contains(postContent).should('be.visible');
      cy.visit(`/profile/${creatorUsername}`);
      cy.contains(postContent).should('be.visible');
      cy.logout();

      cy.login(followerUsername, 'password');
      cy.visit('/');
      cy.contains(postContent).should('be.visible');
    });
  });

  it('a sole creator is warned and then prompted to delete when trying to leave', () => {
    const testId = Date.now();
    const creatorUsername = `creator_${testId}`;
    const groupName = `Solo Creator Delete Test ${testId}`;
    const groupSlug = `solo-creator-delete-test-${testId}`;

    cy.testSetup('create_user', {
      email: `${creatorUsername}@test.com`,
      username: creatorUsername,
      password: 'password',
    }).then(() => {
      cy.login(creatorUsername, 'password');
      cy.visit('/groups');
      cy.get('[data-cy="create-group-button"]').click();
      cy.get('[data-cy="group-name-input"]').type(groupName);
      cy.get('[data-cy="group-description-input"]').type('A group for testing the final solo creator flow.');
      cy.get('[data-cy="create-group-submit-button"]').click();
      cy.url().should('include', `/groups/${groupSlug}`);
      cy.get('[data-cy="group-name-header"]').should('be.visible');

      cy.on('window:alert', (alertText) => {
        expect(alertText).to.contain('As the sole member, leaving the group will permanently delete it.');
      });
      cy.on('window:confirm', (confirmText) => {
        expect(confirmText).to.contain(`Are you sure you want to permanently delete the group "${groupName}"?`);
        return true;
      });

      cy.intercept('DELETE', `**/api/groups/${groupSlug}/`).as('deleteGroup');
      cy.get('[data-cy="group-options-button"]').click();
      cy.contains('a[role="menuitem"]', 'Leave Group').click();
      cy.wait('@deleteGroup');

      cy.url().should('eq', `${Cypress.config().baseUrl}/groups`);
      cy.contains(groupName).should('not.exist');
    });
  });

  // NEW TEST CASE
  it('a creator with members is prompted to transfer ownership when trying to leave', () => {
    const testId = Date.now();
    const creatorUsername = `creator_${testId}`;
    const memberUsername = `member_${testId}`;
    const groupName = `Transfer Owner Test Group ${testId}`;
    const groupSlug = `transfer-owner-test-group-${testId}`;

    cy.testSetup('create_user', {
      email: `${creatorUsername}@test.com`,
      username: creatorUsername,
      password: 'password',
    }).then(() => {
      cy.testSetup('create_user', {
        email: `${memberUsername}@test.com`,
        username: memberUsername,
        password: 'password',
      });
    }).then(() => {
      // Part 1: Creator makes the group
      cy.login(creatorUsername, 'password');
      cy.visit('/groups');
      cy.get('[data-cy="create-group-button"]').click();
      cy.get('[data-cy="group-name-input"]').type(groupName);
      cy.get('[data-cy="group-description-input"]').type('A group for testing transfer ownership flow.');
      cy.get('[data-cy="create-group-submit-button"]').click();
      cy.url().should('include', `/groups/${groupSlug}`).as('groupPageUrl');
      cy.logout();

      // Part 2: Member joins the group
      cy.login(memberUsername, 'password');
      cy.get('@groupPageUrl').then(url => cy.visit(url as unknown as string));
      cy.get('[data-cy="group-membership-button"]').click();
      cy.logout();

      // Part 3: Creator tries to leave and gets prompted
      cy.login(creatorUsername, 'password');
      cy.get('@groupPageUrl').then(url => cy.visit(url as unknown as string));
      
      cy.get('[data-cy="group-options-button"]').click();
      
      // Listen for the alert
      cy.on('window:alert', (alertText) => {
        expect(alertText).to.contain('you must transfer ownership before you can leave');
      });

      // Click "Leave Group" and trigger the alert
      cy.contains('a[role="menuitem"]', 'Leave Group').click();
      
      // Assert the transfer ownership modal is now visible
      cy.contains('h2', 'Transfer Group Ownership').should('be.visible');
    });
  });
});