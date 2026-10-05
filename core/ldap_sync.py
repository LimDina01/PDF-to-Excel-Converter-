def custom_sync_user_relations(user, ldap_attributes, **kwargs):
    """
    This function runs every time a user logs in via Active Directory.
    We use it to strictly enforce that only members of the pdf_convertor group
    can access the application.
    """
    import json
    # Log the attributes to see what we actually received from AD!
    with open("ldap_debug_log.txt", "w") as f:
        f.write(json.dumps({k: str(v) for k, v in ldap_attributes.items()}, indent=4))
        
    ad_groups = ldap_attributes.get("memberOf", [])
    
    # Target group that is allowed to use this app
    TARGET_GROUP = "CN=pdf_convertor,OU=2.Authentication,OU=Other,DC=cbvh66,DC=com"
    
    is_authorized = False
    
    for group in ad_groups:
        if TARGET_GROUP in group:
            is_authorized = True
            break
            
    # ONLY active users can log in to Django.
    # If they are not in the group, their account is instantly deactivated, rejecting their login.
    user.is_active = is_authorized
    
    user.is_staff = False
    user.is_superuser = False
    
    user.save()
