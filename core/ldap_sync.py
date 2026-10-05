def custom_sync_user_relations(user, ldap_attributes, **kwargs):
    """
    This function runs every time a user logs in via Active Directory.
    We use it to check their AD attributes (like Groups) and grant backend Admin access.
    """
    # Active Directory returns 'memberOf' as a list of group strings
    # e.g., ["CN=IT_Admins,OU=Groups,DC=company,DC=local", "CN=Employees,..."]
    
    # We safely get the list of groups, or an empty list if they have none
    ad_groups = ldap_attributes.get("memberOf", [])
    
    # Flag to determine if they get backend access
    is_admin = False
    
    # Loop through their AD groups
    for group in ad_groups:
        # Check if they are a member of a specific Security Group
        # TODO: Change 'IT_Admins' to the actual name of your AD group
        if "CN=IT_Admins" in group: 
            is_admin = True
            break
            
    # Grant backend (Django Admin) access if they are in the group
    user.is_staff = is_admin
    user.is_superuser = is_admin
    user.save()
