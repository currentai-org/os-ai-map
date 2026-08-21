-- Model: entities.packages
-- Dataset: currentai.entities
-- Table: currentai.entities.packages
-- Kind: FULL (daily cron)
--
-- Published packages (NPM, PIP, Go, etc.) linked to AI repos
-- via oso.package_owners_v0 (maps packages to their owner repos).

SELECT DISTINCT
  LOWER(po.package_owner_artifact_namespace || '/' || po.package_owner_artifact_name) AS repo,
  r.project_slug,
  po.package_artifact_source AS package_source,
  po.package_artifact_namespace AS package_namespace,
  po.package_artifact_name AS package_name,
  CASE po.package_artifact_source
    WHEN 'NPM' THEN 'https://www.npmjs.com/package/' || po.package_artifact_name
    WHEN 'PIP' THEN 'https://pypi.org/project/' || po.package_artifact_name
    WHEN 'GO' THEN 'https://pkg.go.dev/' || po.package_artifact_namespace || '/' || po.package_artifact_name
    WHEN 'RUST' THEN 'https://crates.io/crates/' || po.package_artifact_name
    WHEN 'MAVEN' THEN 'https://central.sonatype.com/artifact/' || po.package_artifact_namespace || '/' || po.package_artifact_name
    WHEN 'NUGET' THEN 'https://www.nuget.org/packages/' || po.package_artifact_name
    ELSE ''
  END AS url
FROM oso.package_owners_v0 po
INNER JOIN currentai.entities.repos r
  ON LOWER(po.package_owner_artifact_namespace || '/' || po.package_owner_artifact_name) = r.repo
WHERE po.package_owner_artifact_source = 'GITHUB'
