// C:\Users\Vinay\Project\frontend\cypress\e2e\navigation_ux.cy.ts

describe('Navigation UX Enhancements', () => {
  let scrollTester: any;
  let postAuthor: any;

  beforeEach(() => {
    cy.testSetup('cleanup');

    cy.testSetup('create_user_with_posts', {
      username: 'post_author',
      num_posts: 15,
    }).then((response) => {
      postAuthor = response.body;
    });

    cy.testSetup('create_user', { username_prefix: 'scroll_tester' }).then((response) => {
      scrollTester = response.body;
      
      cy.testSetup('create_follow', {
        follower: scrollTester.username,
        following: postAuthor.username,
      }).then(() => {
        cy.login(scrollTester.username, 'Airtel@123');
      });
    });
  });

  // Helper function for the scroll test pattern
  const testScrollToTop = (url: string, selectorToWaitFor: string, linkSelector: string) => {
    cy.visit(url);
    cy.get(selectorToWaitFor, { timeout: 10000 }).should('be.visible');
    cy.scrollTo('bottom', { duration: 500 });
    cy.window().its('scrollY').should('not.eq', 0);
    cy.get(linkSelector).click();
    cy.window().its('scrollY').should('eq', 0);
  };

  context('Desktop Viewport (1280x720)', () => {
    beforeEach(() => {
      cy.viewport(1280, 720);
    });

    it('should scroll to the top when clicking the logo link while on the home feed', () => {
      // --- THIS IS THE FIX ---
      testScrollToTop('/', '[data-cy="post-container"]', '[data-cy="navbar-logo-link"]');
    });

    it('should scroll to the top when clicking the sidebar home link while on the home feed', () => {
      // --- THIS IS THE FIX ---
      testScrollToTop('/', '[data-cy="post-container"]', '[data-cy="sidebar-home-link"]');
    });

    it('should scroll to the top when clicking the profile link while on the profile page', () => {
      cy.testSetup('create_user_with_posts', { username: scrollTester.username, num_posts: 15 });
      testScrollToTop(`/profile/${scrollTester.username}`, '[data-cy="profile-picture-container"]', '[data-cy="profile-link"]');
    });

    it('should scroll to the top when clicking the my groups link while on the groups page', () => {
      for (let i = 0; i < 10; i++) {
        cy.testSetup('create_group', {
          creator_username: scrollTester.username,
          name: `Scroll Test Group ${i}`
        });
      }
      testScrollToTop('/groups', 'h1:contains("Discover Groups")', '[data-cy="sidebar-groups-link"]');
    });
  });

  context('Default Viewport', () => {
    it('should scroll to the top when clicking the notifications link while on the notifications page', () => {
      cy.visit('/notifications');
      cy.get('h1').contains('Your Notifications').should('be.visible');
      cy.scrollTo('bottom', { ensureScrollable: false });
      cy.get('[data-cy="navbar-notifications-link"]').click();
      cy.window().its('scrollY').should('eq', 0);
    });

    it('should scroll to the top when clicking the saved posts link while on the saved posts page', () => {
      cy.visit('/saved-posts');
      cy.get('h1').contains('Saved Posts').should('be.visible');
      cy.scrollTo('bottom', { ensureScrollable: false });
      cy.get('[data-cy="sidebar-saved-posts-link"]').click({ force: true });
      cy.window().its('scrollY').should('eq', 0);
    });
  });
});