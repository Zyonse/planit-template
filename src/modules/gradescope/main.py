import dateparser
from src.modules.interfaces import Module


class Gradescope(Module):
    ROOT = 'https://www.gradescope.com'

    def _init(self):
        # Extract authentication token from login page
        login_page_res = self.session.get(Gradescope.ROOT)
        login_page = Module.parse_html(login_page_res.text)
        token = None
        for form in login_page.find_all('form'):
            if form.get('action') == '/login':
                for input_element in form.find_all('input'):
                    if input_element.get('name') == 'authenticity_token':
                        token = input_element.get('value')

        if token is not None:
            # Login by imitating JSON payload found by:
            # Inspect -> Network -> Enter info and login -> View 'login' request payload
            login_payload = {
                'utf8': '✓',
                'authenticity_token': token,
                'session[email]': self.user,
                'session[password]': self.password,
                'session[remember_me]': 0,
                'commit': 'Log In',
                'session[remember_me_sso]': 0
            }
            login_response = self.session.post(
                Gradescope.ROOT + '/login',
                params=login_payload
            )
            if login_response.status_code == 200:
                self.initialized = True

    def _main(self, assignments):
        dashboard_res = self.session.get(Gradescope.ROOT + '/account')
        dashboard = Module.parse_html(dashboard_res.text)

        courses = dashboard.find('div', {'class': 'courseList--coursesForTerm'})
        for course in courses.find_all('a', {'class': 'courseBox'}):
            course_name = course.find('h3', {'class': 'courseBox--shortname'}).text
            course_link = course.get('href')

            # Retrieve assignment information
            course_dashboard_res = self.session.get(Gradescope.ROOT + course_link)
            course_dashboard = Module.parse_html(course_dashboard_res.text)
            assignment_table = course_dashboard.find('tbody')
            for row in assignment_table.find_all('tr', {'role': 'row'}):
                title = Gradescope._get_assignment_title(row)
                date_string = Gradescope._get_assignment_due_date(row)
                due_date = dateparser.parse(date_string)
                status = Gradescope._get_assignment_status(row)
                done = (status != 'No Submission')
                print(course_name, status, due_date)

    @staticmethod
    def _get_assignment_title(row):
        """Returns the title of an assignment given its row in the table."""

        heading = row.find('th')
        title = heading.find('a')
        if title is None:
            title = heading.find('button')
        if title is None:
            title = heading
        return title.text

    @staticmethod
    def _get_assignment_due_date(row):
        """Returns the title of an assignment given its row in the table."""

        return row.find('span', {'class': 'submissionTimeChart--dueDate'}).text

    @staticmethod
    def _get_assignment_status(row):
        """Returns the title of an assignment given its row in the table."""

        return row.find('div', {'class': 'submissionStatus--text'}).text


if __name__ == '__main__':
    arr = []
    test = Gradescope()
    test.run(arr)
