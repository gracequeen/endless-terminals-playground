I'm migrating our microservices infrastructure from one cloud provider to another, and I need to audit our container base images to ensure we're not carrying unnecessary packages that bloat our deployments and increase our attack surface.

I have a list of packages currently installed in our production Ubuntu-based container at /home/user/migration/installed_packages.txt (one package name per line). I also have a manifest of packages we actually need for our services at /home/user/migration/required_packages.txt (also one package name per line).

Here's what I need you to do:

1. **Identify removable packages**: Find all packages in installed_packages.txt that are NOT in required_packages.txt. But here's the catch — some of those "extra" packages might be dependencies of required packages. Use apt-cache or apt-rdepends to check the dependency tree of each required package, and don't mark a package as removable if it's a dependency (direct or transitive, up to 3 levels deep) of any required package.

2. **Calculate space savings**: For each truly removable package, get its installed size using dpkg-query or apt-cache show. Sum up the total space we'd save.

3. **Check for security updates**: For each removable package, check if there's a security update available (the package version in the installed list might be outdated). You can parse apt-cache policy output or check against the Ubuntu security pocket.

4. **Generate the migration report**: Write your findings to /home/user/migration/removal_report.json in this exact format:

```json
{
  "summary": {
    "total_installed": <int>,
    "total_required": <int>,
    "removable_count": <int>,
    "kept_as_dependencies": <int>,
    "total_space_savings_kb": <int>
  },
  "removable_packages": [
    {
      "name": "<package_name>",
      "installed_version": "<version>",
      "size_kb": <int>,
      "has_security_update": <boolean>
    }
  ],
  "dependency_protected": [
    {
      "name": "<package_name>",
      "required_by": ["<package_that_needs_it>", ...]
    }
  ]
}
```

The `removable_packages` array must be sorted alphabetically by package name. The `dependency_protected` array should list packages that were in installed but not in required, yet couldn't be removed because they're dependencies — also sorted alphabetically.

5. **Create an uninstall script**: Generate /home/user/migration/remove_packages.sh that, if executed with sudo, would remove all the removable packages in a single apt-get remove command. The script should have a shebang, be executable, and include a dry-run echo statement before the actual removal command.

Make sure the JSON is valid and properly formatted. I'll be parsing this programmatically for our migration pipeline.
