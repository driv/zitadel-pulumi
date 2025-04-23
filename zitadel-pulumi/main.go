package main

import (
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
	"github.com/pulumiverse/pulumi-zitadel/sdk/go/zitadel"
)

type Role struct {
	RoleKey     string
	DisplayName string
	Group       string
}

func createRole(ctx *pulumi.Context, projectID pulumi.IDOutput, role Role) (*zitadel.ProjectRole, error) {
	return zitadel.NewProjectRole(ctx, role.RoleKey, &zitadel.ProjectRoleArgs{
		ProjectId:   projectID,
		RoleKey:     pulumi.String(role.RoleKey),
		DisplayName: pulumi.String(role.DisplayName),
		Group:       pulumi.String(role.Group),
	})
}

func main() {
	pulumi.Run(func(ctx *pulumi.Context) error {
		proj, err := zitadel.NewProject(ctx, "infrastructure", &zitadel.ProjectArgs{
			ProjectRoleAssertion: pulumi.Bool(true),
		})
		if err != nil {
			return err
		}

		if _, err := createRole(ctx, proj.ID(), Role{"admin", "Administrator", "Admins"}); err != nil {
			return err
		}
		if _, err := createRole(ctx, proj.ID(), Role{"editor", "Editor", "Editors"}); err != nil {
			return err
		}
		if _, err := createRole(ctx, proj.ID(), Role{"viewer", "Viewer", "Viewers"}); err != nil {
			return err
		}

		grafanaApp, err := zitadel.NewApplicationOidc(ctx, "grafana", &zitadel.ApplicationOidcArgs{
			ProjectId: proj.ID(),
			RedirectUris: pulumi.StringArray{
				pulumi.String("https://grafana.local.amazinglyabstract.it/login/generic_oauth"),
			},
			PostLogoutRedirectUris: pulumi.StringArray{
				pulumi.String("https://grafana.local.amazinglyabstract.it/login"),
			},
			AppType:                  pulumi.String("OIDC_APP_TYPE_WEB"),
			IdTokenUserinfoAssertion: pulumi.Bool(true),
			GrantTypes: pulumi.StringArray{
				pulumi.String("OIDC_GRANT_TYPE_REFRESH_TOKEN"),
				pulumi.String("OIDC_GRANT_TYPE_AUTHORIZATION_CODE"),
			},
			ResponseTypes: pulumi.StringArray{
				pulumi.String("OIDC_RESPONSE_TYPE_CODE"),
			},
			AuthMethodType: pulumi.String("OIDC_AUTH_METHOD_TYPE_NONE"),
		})
		if err != nil {
			return err
		}

		ctx.Export("grafanaAppId", grafanaApp.ID())
		ctx.Export("projectId", proj.ID())
		return nil
	})
}
