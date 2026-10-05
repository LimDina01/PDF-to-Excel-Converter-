def custom_sync_user_relations(user, ldap_attributes, **kwargs):
    """
    This function runs every time a user logs in via Active Directory.
    We use it to strictly enforce that only members of the pdf_convertor group
    can access the application.
    """
    # Active Directory returns 'memberOf' as a list of group strings
    ad_groups = ldap_attributes.get("memberOf", [])
    
    # Target group that is allowed to use this app
    TARGET_GROUP = "CN=pdf_convertor,OU=2.Authentication,OU=Other,DC=cbvh66,DC=com"
    
    # Flag to determine if they are authorized
    is_authorized = False
    
    # Loop through their AD groups to see if they are in the target group
    for group in ad_groups:
        if TARGET_GROUP in group:
            is_authorized = True
            break
            
    # ONLY active users can log in to Django.
    # If they are not in the group, their account is instantly deactivated, rejecting their login.
    user.is_active = is_authorized
    
    # We will not make them an admin by default, just a standard active user
    user.is_staff = False
    user.is_superuser = False
    
    user.save()
