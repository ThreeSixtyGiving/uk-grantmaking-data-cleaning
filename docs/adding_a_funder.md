# Adding a funder

Adding a funder is done through the new grantmaker page. Use the form below to add the funder. 

You need the Org ID for the funder. If this org ID already exists you'll be redirected to the 
funder page. If the Org ID already exists you'll be taken to its page. If the Org ID has
data in Find that Charity then it will load in that data, otherwise you'll need to fill
in the details for the funder.

<form action="/grantmakers/funder/new" method="GET" class="filters">
<div>
<label for="id_org_id">New funder org ID:</label>
<input type="text" name="org_id" required="" id="id_org_id">
</div>
<input type="submit" value="Add new funder" class="btn btn-primary">
</form>